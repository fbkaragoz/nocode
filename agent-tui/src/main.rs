mod model;
mod logic;
mod ui;
mod db;
mod sandbox;

use std::{
    io,
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::sync::Mutex;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use crate::model::{GameState, RegistrationRequest, AgentProvider};
use axum::{
    routing::post,
    extract::State,
    Json, Router,
};
use tower_http::cors::CorsLayer;

async fn register_agent(
    State(state): State<Arc<Mutex<GameState>>>,
    Json(payload): Json<RegistrationRequest>,
) -> Json<serde_json::Value> {
    let mut state = state.lock().await;
    state.logs.push(format!("New agent registered: {} ({:?})", payload.name, payload.provider));
    state.add_agent(&payload.name, payload.provider, payload.model, payload.endpoint);
    Json(serde_json::Value::String("Registered".to_string()))
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load environment variables
    let _ = dotenvy::dotenv();

    // Shared State
    let state = Arc::new(Mutex::new(GameState::new()));

    // Load agents from JSON config
    let config_path = "agents.json";
    if let Ok(content) = std::fs::read_to_string(config_path) {
        if let Ok(agents_info) = serde_json::from_str::<Vec<serde_json::Value>>(&content) {
            let mut s = state.lock().await;
            for info in agents_info {
                let name = info["name"].as_str().unwrap_or("Unknown");
                let provider_str = info["provider"].as_str().unwrap_or("External");
                let model = info["model"].as_str().map(|s| s.to_string());
                
                let provider = match provider_str {
                    "OpenAI" => AgentProvider::OpenAI,
                    "Gemini" => AgentProvider::Gemini,
                    "OpenRouter" => AgentProvider::OpenRouter,
                    "GLM" => AgentProvider::GLM,
                    _ => AgentProvider::External,
                };
                
                s.add_agent(name, provider, model, None);
            }
            let agent_count = s.agents.len();
            s.logs.push(format!("Loaded {} agents from agents.json", agent_count));
        }
    } else {
        // Fallback: Auto-register agents from environment if no JSON
        let mut s = state.lock().await;
        if std::env::var("OPENAI_API_KEY").is_ok() {
            s.add_agent("OpenAI-v4", AgentProvider::OpenAI, None, None);
        }
        if std::env::var("GEMINI_API_KEY").is_ok() {
            s.add_agent("Gemini-Flash", AgentProvider::Gemini, None, None);
        }
        if std::env::var("GLM_API_KEY").is_ok() {
            s.add_agent("GLM-4", AgentProvider::GLM, None, None);
        }
        if std::env::var("OPENROUTER_API_KEY").is_ok() {
            s.add_agent("OpenRouter-Claude", AgentProvider::OpenRouter, None, None);
        }
    }

    // Use a cancellation token for graceful shutdown
    let (tx, mut rx) = tokio::sync::mpsc::channel::<()>(1);
    let tx_clone = tx.clone();

    // Spawn API Server
    let api_state = Arc::clone(&state);
    tokio::spawn(async move {
        let app = Router::new()
            .route("/register", post(register_agent))
            .layer(CorsLayer::permissive())
            .with_state(api_state);

        let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
        axum::serve(listener, app).await.unwrap();
    });

    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let tick_rate = Duration::from_millis(500);
    let mut last_tick = Instant::now();

    loop {
        {
            let current_state = state.lock().await;
            terminal.draw(|f| ui::render(f, &current_state))?;
        }

        if event::poll(Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') => {
                        let _ = tx_clone.send(()).await;
                        break;
                    },
                    KeyCode::Char('j') | KeyCode::Down => {
                        let mut s = state.lock().await;
                        if s.scroll_offset + 1 < s.logs.len() {
                            s.scroll_offset += 1;
                        }
                    },
                    KeyCode::Char('k') | KeyCode::Up => {
                        let mut s = state.lock().await;
                        if s.scroll_offset > 0 {
                            s.scroll_offset -= 1;
                        }
                    },
                    KeyCode::PageDown => {
                        let mut s = state.lock().await;
                        s.scroll_offset = s.scroll_offset.saturating_add(10).min(s.logs.len().saturating_sub(1));
                    },
                    KeyCode::PageUp => {
                        let mut s = state.lock().await;
                        s.scroll_offset = s.scroll_offset.saturating_sub(10);
                    },
                    KeyCode::Char('e') | KeyCode::Char('E') => {
                        let s = state.lock().await;
                        let export_path = format!("conversation_day_{}.txt", s.day);
                        if let Ok(mut f) = std::fs::File::create(&export_path) {
                            use std::io::Write;
                            for log in &s.logs {
                                let _ = writeln!(f, "{}", log);
                            }
                            drop(s);
                            let mut s2 = state.lock().await;
                            s2.logs.push(format!("Exported to {}", export_path));
                        }
                    },
                    KeyCode::Home => {
                        let mut s = state.lock().await;
                        s.scroll_offset = 0;
                    },
                    KeyCode::End => {
                        let mut s = state.lock().await;
                        s.scroll_offset = s.logs.len().saturating_sub(1);
                    },
                    KeyCode::Char(' ') => {
                        // Auto-scroll to bottom
                        let mut s = state.lock().await;
                        s.scroll_offset = s.logs.len().saturating_sub(18);
                    },
                    _ => {}
                }
            }
        }

        if last_tick.elapsed() >= tick_rate {
            let state_clone = Arc::clone(&state);
            tokio::spawn(async move {
                let mut guard = state_clone.lock().await;
                logic::run_step(&mut guard).await;
            });
            last_tick = Instant::now();
        }

        // Check if we should exit
        if rx.try_recv().is_ok() {
            break;
        }
    }

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    Ok(())
}
