use ratatui::{
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
    Frame,
    text::{Line, Span},
};
use crate::model::{GameState, AgentRole, GamePhase};

pub fn render(f: &mut Frame, state: &GameState) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints(
            [
                Constraint::Length(3),  // Header
                Constraint::Length(3),  // Status Bar
                Constraint::Length(10), // Agents
                Constraint::Min(18),    // Logs (EXPANDED)
            ]
            .as_ref(),
        )
        .split(f.size());

    // --- Header ---
    let header_text = "🎭 MAFIA: KASABA GECESİ 🐺";
    let header = Paragraph::new(header_text)
        .style(Style::default().fg(Color::Red).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::ALL).title(" OYUN "));
    f.render_widget(header, chunks[0]);

    // --- Status Bar (Day/Phase) ---
    let (phase_name, phase_color) = match state.phase {
        GamePhase::Night => ("🌙 GECE", Color::Blue),
        GamePhase::Dawn => ("🌅 ŞAFAK", Color::Yellow),
        GamePhase::Discussion => ("💬 TARTIŞMA", Color::Green),
        GamePhase::Vote => ("🗳️ OY", Color::Magenta),
        GamePhase::GameOver => ("🏆 OYUN BİTTİ", Color::Red),
    };
    let alive = state.alive_agents().len();
    let total = state.agents.len();
    let status_text = format!("Gün {} | {} | Hayatta: {}/{} | [j/k:Scroll Space:Son E:Export q:Çık]", 
        state.day, phase_name, alive, total);
    let status = Paragraph::new(status_text)
        .style(Style::default().fg(phase_color))
        .block(Block::default().borders(Borders::ALL));
    f.render_widget(status, chunks[1]);

    // --- Agent List ---
    let agents: Vec<ListItem> = state
        .agents
        .iter()
        .map(|a| {
            // Role and status
            let (role_icon, mut style) = match (&a.role, a.is_alive) {
                (AgentRole::Dead, _) => ("💀", Style::default().fg(Color::DarkGray)),
                (AgentRole::Monster, true) => ("🐺", Style::default().fg(Color::Red)), // Hidden in real game
                (AgentRole::Villager, true) => ("👤", Style::default().fg(Color::White)),
                _ => ("❓", Style::default().fg(Color::Gray)),
            };

            // Thinking indicator
            if a.is_thinking {
                style = style.fg(Color::LightBlue);
            }

            // Personality emoji
            let personality_emoji = match a.personality.as_deref() {
                Some(p) if p.contains("paranoid") => "😰",
                Some(p) if p.contains("trusting") => "😊",
                Some(p) if p.contains("aggressive") => "😠",
                Some(p) if p.contains("calm") => "😌",
                Some(p) if p.contains("manipulative") => "🎭",
                Some(p) if p.contains("nervous") => "😬",
                Some(p) if p.contains("confident") => "😎",
                Some(p) if p.contains("quiet") => "🤫",
                Some(p) if p.contains("dramatic") => "🎭",
                Some(p) if p.contains("logical") => "🧠",
                _ => "🤖",
            };

            let status_icon = if a.is_thinking { "⏳" } else if !a.is_alive { "💀" } else { "✓" };
            
            // Suspicion target
            let suspicion = a.suspicion_target.as_ref()
                .map(|t| format!(" → {}", t.chars().take(8).collect::<String>()))
                .unwrap_or_default();

            ListItem::new(Line::from(vec![
                Span::styled(format!("{} ", role_icon), style),
                Span::styled(format!("{:<10} ", a.name.chars().take(10).collect::<String>()), style),
                Span::raw(format!("{} {}{}", personality_emoji, status_icon, suspicion)),
            ]))
        })
        .collect();

    let agent_list = List::new(agents)
        .block(Block::default().borders(Borders::ALL).title(" KASABALILAR "));
    f.render_widget(agent_list, chunks[2]);

    // --- Logs (Scrollable Paragraph) ---
    let visible_height = 16;
    let total_logs = state.logs.len();
    let start = state.scroll_offset.min(total_logs.saturating_sub(visible_height));
    let end = (start + visible_height).min(total_logs);
    
    let log_content: Vec<Line> = state.logs.get(start..end).unwrap_or(&[]).iter().map(|log| {
        let style = if log.contains("---") || log.contains("🌙") || log.contains("🌅") {
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else if log.contains("🏆") || log.contains("💀") {
            Style::default().fg(Color::Green).add_modifier(Modifier::BOLD)
        } else if log.contains("⚖️") {
            Style::default().fg(Color::Magenta)
        } else if log.contains("🗳️") {
            Style::default().fg(Color::Cyan)
        } else if log.contains("Error") || log.contains("😢") {
            Style::default().fg(Color::Red)
        } else {
            Style::default().fg(Color::Gray)
        };
        Line::from(Span::styled(log.clone(), style))
    }).collect();

    let scroll_info = format!(" GÜNLÜK [{}/{}] ", start + 1, total_logs.max(1));
    let logs = Paragraph::new(log_content)
        .block(Block::default().borders(Borders::ALL).title(scroll_info))
        .wrap(Wrap { trim: true });
    f.render_widget(logs, chunks[3]);
}
