use rusqlite::{params, Connection, Result};

#[derive(Debug)]
pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new() -> Result<Self> {
        let conn = Connection::open("agents.db")?;
        conn.execute(
            "CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                round INTEGER,
                agent_name TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        Ok(Database { conn })
    }

    pub fn save_turn(&self, round: u32, agent_name: &str, message: &str) -> Result<()> {
        self.conn.execute(
            "INSERT INTO conversations (round, agent_name, message) VALUES (?1, ?2, ?3)",
            params![round, agent_name, message],
        )?;
        Ok(())
    }
}
