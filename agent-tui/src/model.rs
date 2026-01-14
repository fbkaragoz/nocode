use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum AgentRole {
    Monster,   // The killer - acts at night
    Villager,  // Normal townsperson
    Dead,      // Eliminated
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum AgentProvider {
    OpenAI,
    Gemini,
    GLM,
    OpenRouter,
    External,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum GamePhase {
    Night,       // Monster picks victim
    Dawn,        // Announce death
    Discussion,  // Everyone talks (max 10*N turns)
    Vote,        // Eliminate or pass
    GameOver,    // Winner declared
}

use crate::db::Database;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Agent {
    pub id: String,
    pub name: String,
    pub score: u32,
    pub role: AgentRole,
    pub provider: AgentProvider,
    pub model: Option<String>,
    pub endpoint: Option<String>,
    pub personality: Option<String>,
    // Mafia-specific fields
    pub is_alive: bool,
    pub suspicion_target: Option<String>,  // Who they accuse
    pub vote_target: Option<String>,        // Who they vote to eliminate
    pub memory: Vec<String>,                // Past statements for consistency
    #[serde(skip)]
    pub is_thinking: bool,
    #[serde(skip)]
    pub error_count: u32,
}

impl Agent {
    pub fn new(id: &str, name: &str, provider: AgentProvider, model: Option<String>, endpoint: Option<String>) -> Self {
        // Random personality traits for villagers
        let personalities = [
            "paranoid and suspicious",
            "trusting and naive", 
            "aggressive and accusatory",
            "calm and analytical",
            "manipulative and cunning",
            "nervous and defensive",
            "confident and assertive",
            "quiet and observant",
            "dramatic and emotional",
            "logical and methodical",
        ];
        let random_idx = (std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos() as usize + id.len() * 7) % personalities.len();
        let personality = Some(personalities[random_idx].to_string());

        Self {
            id: id.to_string(),
            name: name.to_string(),
            score: 0,
            role: AgentRole::Villager,
            provider,
            model,
            endpoint,
            personality,
            is_alive: true,
            suspicion_target: None,
            vote_target: None,
            memory: Vec::new(),
            is_thinking: false,
            error_count: 0,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GameState {
    pub agents: Vec<Agent>,
    pub day: u32,                        // Current day in game
    pub phase: GamePhase,
    pub logs: Vec<String>,
    pub discussion_turns: u32,           // Turns used in current discussion
    pub last_victim: Option<String>,     // Who died last night
    pub last_eliminated: Option<String>, // Who was voted out
    #[serde(skip)]
    pub db: Option<Database>,
    #[serde(skip)]
    pub scroll_offset: usize,
}

#[derive(Deserialize, Serialize)]
pub struct RegistrationRequest {
    pub name: String,
    pub provider: AgentProvider,
    pub model: Option<String>,
    pub endpoint: Option<String>,
}

impl GameState {
    pub fn new() -> Self {
        let db = Database::new().ok();
        Self {
            agents: Vec::new(),
            day: 1,
            phase: GamePhase::Night,  // Game starts at night
            logs: Vec::new(),
            discussion_turns: 0,
            last_victim: None,
            last_eliminated: None,
            db,
            scroll_offset: 0,
        }
    }

    pub fn add_agent(&mut self, name: &str, provider: AgentProvider, model: Option<String>, endpoint: Option<String>) {
        let id = format!("agent-{}", self.agents.len() + 1);
        self.agents.push(Agent::new(&id, name, provider, model, endpoint));
    }

    pub fn get_monster(&self) -> Option<&Agent> {
        self.agents.iter().find(|a| a.role == AgentRole::Monster && a.is_alive)
    }

    pub fn alive_agents(&self) -> Vec<&Agent> {
        self.agents.iter().filter(|a| a.is_alive).collect()
    }

    pub fn alive_villagers(&self) -> Vec<&Agent> {
        self.agents.iter().filter(|a| a.is_alive && a.role == AgentRole::Villager).collect()
    }

    pub fn assign_monster(&mut self) {
        // Randomly assign one agent as monster
        if self.agents.is_empty() { return; }
        let random_idx = (std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos() as usize) % self.agents.len();
        self.agents[random_idx].role = AgentRole::Monster;
    }
}
