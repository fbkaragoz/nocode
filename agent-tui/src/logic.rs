use crate::model::{AgentRole, GamePhase, GameState, Agent};
use reqwest::Client;
use tokio::task::JoinSet;

async fn call_provider(agent: &Agent, system_prompt: &str, user_prompt: &str) -> Result<String, String> {
    let client = Client::new();
    
    match agent.provider {
        crate::model::AgentProvider::OpenAI => {
            let api_key = std::env::var("OPENAI_API_KEY").map_err(|_| "No OpenAI key")?;
            let model = agent.model.as_deref().unwrap_or("gpt-4o-mini");
            let resp = client.post("https://api.openai.com/v1/chat/completions")
                .header("Authorization", format!("Bearer {}", api_key))
                .json(&serde_json::json!({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_completion_tokens": 500
                }))
                .send()
                .await.map_err(|e| e.to_string())?;
            
            if !resp.status().is_success() {
                let err = resp.text().await.unwrap_or_default();
                return Err(format!("OpenAI Error: {}", err.chars().take(100).collect::<String>()));
            }
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json["choices"][0]["message"]["content"].as_str().unwrap_or("").to_string())
        },
        crate::model::AgentProvider::Gemini => {
            let api_key = std::env::var("GEMINI_API_KEY").map_err(|_| "No Gemini key")?;
            let model = agent.model.as_deref().unwrap_or("gemini-2.0-flash");
            let url = format!("https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}", model, api_key);
            let resp = client.post(&url)
                .json(&serde_json::json!({
                    "contents": [{"parts": [{"text": format!("{}\n\n{}", system_prompt, user_prompt)}]}],
                    "generationConfig": {"maxOutputTokens": 500}
                }))
                .send()
                .await.map_err(|e| e.to_string())?;
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json["candidates"][0]["content"]["parts"][0]["text"].as_str().unwrap_or("").to_string())
        },
        crate::model::AgentProvider::OpenRouter => {
            let api_key = std::env::var("OPENROUTER_API_KEY").map_err(|_| "No OpenRouter key")?;
            let model = agent.model.as_deref().unwrap_or("deepseek/deepseek-chat-v3-0324");
            let resp = client.post("https://openrouter.ai/api/v1/chat/completions")
                .header("Authorization", format!("Bearer {}", api_key))
                .json(&serde_json::json!({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_completion_tokens": 500
                }))
                .send()
                .await.map_err(|e| e.to_string())?;
            if !resp.status().is_success() {
                let err = resp.text().await.unwrap_or_default();
                return Err(format!("Router Error: {}", err.chars().take(100).collect::<String>()));
            }
            let json: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
            Ok(json["choices"][0]["message"]["content"].as_str().unwrap_or("").to_string())
        },
        _ => Ok(format!("[{}]: External/GLM placeholder", agent.name)),
    }
}

pub async fn run_step(state: &mut GameState) {
    if state.agents.is_empty() { return; }

    // Assign monster on first night if not done
    if state.day == 1 && state.phase == GamePhase::Night && state.get_monster().is_none() {
        state.assign_monster();
        let monster_name = state.get_monster().map(|m| m.name.clone()).unwrap_or_default();
        // SECRET REVEAL for game master (you!)
        state.logs.push(format!("🔒 [GİZLİ] Canavar: {} 🐺", monster_name));
        state.logs.push(format!("🌙 GECE {} - Kasaba uykuya dalıyor...", state.day));
    }

    let alive_count = state.alive_agents().len();
    let villager_count = state.alive_villagers().len();
    
    // Win condition checks
    if state.get_monster().is_none() {
        state.logs.push("🏆 KÖYLÜLER KAZANDI! Canavar elendi!".to_string());
        state.phase = GamePhase::GameOver;
        return;
    }
    if villager_count <= 1 {
        let monster = state.get_monster().map(|m| m.name.clone()).unwrap_or_default();
        state.logs.push(format!("💀 CANAVAR KAZANDI! {} herkesi yok etti!", monster));
        state.phase = GamePhase::GameOver;
        return;
    }

    match state.phase {
        GamePhase::Night => {
            // Monster picks a victim
            let monster = state.get_monster().cloned();
            if let Some(monster) = monster {
                let alive_victims: Vec<String> = state.agents.iter()
                    .filter(|a| a.is_alive && a.role != AgentRole::Monster)
                    .map(|a| a.name.clone())
                    .collect();
                
                if alive_victims.is_empty() {
                    state.phase = GamePhase::GameOver;
                    return;
                }

                // Monster chooses
                if let Some(m) = state.agents.iter_mut().find(|a| a.role == AgentRole::Monster) {
                    m.is_thinking = true;
                }
                
                let victim_list = alive_victims.join(", ");
                let system = "You are the monster. Pick ONE victim to eliminate. Reply with ONLY their exact name.";
                let prompt = format!("Living villagers: {}. Who do you kill tonight?", victim_list);
                
                let response = call_provider(&monster, system, &prompt).await;
                
                if let Some(m) = state.agents.iter_mut().find(|a| a.role == AgentRole::Monster) {
                    m.is_thinking = false;
                }

                if let Ok(victim_name) = response {
                    let victim_name = victim_name.trim().to_string();
                    // Kill the victim
                    for a in &mut state.agents {
                        if a.name.to_lowercase().contains(&victim_name.to_lowercase()) && a.role != AgentRole::Monster {
                            a.is_alive = false;
                            a.role = AgentRole::Dead;
                            state.last_victim = Some(a.name.clone());
                            break;
                        }
                    }
                }
            }
            state.phase = GamePhase::Dawn;
        },

        GamePhase::Dawn => {
            // Announce the death
            if let Some(victim) = &state.last_victim {
                state.logs.push(format!("🌅 ŞAFAK - {} ölü bulundu!", victim));
            } else {
                state.logs.push("🌅 ŞAFAK - Kimse ölmedi! (Tuhaf...)".to_string());
            }
            state.discussion_turns = 0;
            state.phase = GamePhase::Discussion;
        },

        GamePhase::Discussion => {
            // Discussion is now SEQUENTIAL - one agent at a time
            // Each agent sees what others said before responding
            
            let alive: Vec<Agent> = state.agents.iter().filter(|a| a.is_alive).cloned().collect();
            let other_names: Vec<String> = alive.iter().map(|a| a.name.clone()).collect();
            let max_turns = 3; // 3 rounds of discussion
            
            if state.discussion_turns >= max_turns {
                state.logs.push("".to_string());
                state.logs.push("⏰ Tartışma süresi doldu! Oy verme zamanı...".to_string());
                state.phase = GamePhase::Vote;
                return;
            }

            state.logs.push(format!("--- TARTIŞMA TURU {} ---", state.discussion_turns + 1));
            
            // Build recent conversation context (last 5 messages)
            // IMPORTANT: Filter out secret logs so agents can't cheat!
            let recent_context: String = state.logs.iter()
                .rev()
                .filter(|l| l.contains(": ") && !l.contains("GİZLİ") && !l.contains("🔒"))
                .take(5)
                .cloned()
                .collect::<Vec<_>>()
                .into_iter()
                .rev()
                .collect::<Vec<_>>()
                .join(" | ");

            // SEQUENTIAL: Each agent speaks one at a time
            for agent in &state.agents.clone() {
                if !agent.is_alive { continue; }
                
                // Mark thinking
                if let Some(a) = state.agents.iter_mut().find(|a| a.id == agent.id) {
                    a.is_thinking = true;
                }
                
                // Auto-scroll to bottom
                state.scroll_offset = state.logs.len().saturating_sub(16);
                
                let personality = agent.personality.as_deref().unwrap_or("neutral");
                let role_hint = if agent.role == AgentRole::Monster {
                    "You are the WEREWOLF 🐺! Act innocent, deflect blame, accuse others convincingly. Be dramatic!"
                } else {
                    "You are a VILLAGER. Find the werewolf! Be suspicious, dramatic, and accusatory. Trust no one!"
                };
                
                let last_victim = state.last_victim.clone().unwrap_or("nobody".to_string());
                
                let system = format!("MAFIA GAME: You are {} playing as a {} villager. {}. \
                    Be DRAMATIC and EMOTIONAL! Use accusations like 'I ACCUSE {}!' or 'I TRUST {}'. \
                    Keep it SHORT (1-2 sentences) but INTENSE!", 
                    agent.name, personality, role_hint, 
                    other_names.first().unwrap_or(&"someone".to_string()),
                    other_names.last().unwrap_or(&"someone".to_string()));
                
                let prompt = format!("🔪 {} was MURDERED last night! \
                    Survivors: {}. \
                    Previous accusations: {}. \
                    WHO IS THE KILLER? React dramatically!", 
                    last_victim, other_names.join(", "), recent_context);
                // Get agent's memory for consistency
                let my_past = agent.memory.iter().take(3).cloned().collect::<Vec<_>>().join(" | ");
                
                let response = call_provider(&agent, &system, &format!("{} YOUR PAST STATEMENTS: [{}]", prompt, my_past)).await;
                
                // Clear thinking
                if let Some(a) = state.agents.iter_mut().find(|a| a.id == agent.id) {
                    a.is_thinking = false;
                }
                
                if let Ok(speech) = response {
                    let speech = speech.chars().take(400).collect::<String>();
                    
                    // SAVE TO MEMORY for consistency
                    if let Some(a) = state.agents.iter_mut().find(|a| a.id == agent.id) {
                        a.memory.push(speech.clone());
                        // Keep only last 5 memories
                        if a.memory.len() > 5 { a.memory.remove(0); }
                    }
                    
                    // Add to logs
                    state.logs.push(format!("{}: {}", agent.name, speech));
                    
                    // Extract accusation
                    for other in &other_names {
                        if speech.to_lowercase().contains(&other.to_lowercase()) && other != &agent.name {
                            if speech.to_lowercase().contains("accuse") || speech.to_lowercase().contains("suspect") {
                                if let Some(a) = state.agents.iter_mut().find(|a| a.id == agent.id) {
                                    a.suspicion_target = Some(other.clone());
                                }
                                break;
                            }
                        }
                    }
                    
                    // Auto-scroll to show new message
                    state.scroll_offset = state.logs.len().saturating_sub(16);
                }
                
                // Delay between speakers (2 seconds)
                tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
            }

            state.discussion_turns += 1;
        },

        GamePhase::Vote => {
            // Each alive agent votes
            let alive: Vec<Agent> = state.agents.iter().filter(|a| a.is_alive).cloned().collect();
            let names: Vec<String> = alive.iter().map(|a| a.name.clone()).collect();
            
            let mut set = JoinSet::new();
            for agent in &mut state.agents {
                if !agent.is_alive { continue; }
                agent.is_thinking = true;
                let agent_clone = agent.clone();
                let names_clone = names.clone();
                
                set.spawn(async move {
                    let role_hint = if agent_clone.role == AgentRole::Monster {
                        "Vote for an innocent to eliminate them, or vote PASS to avoid suspicion."
                    } else {
                        "Vote for who you think is the monster, or PASS if unsure."
                    };
                    
                    let system = format!("{}. Reply with ONLY a name or PASS.", role_hint);
                    let prompt = format!("Vote to eliminate from: {}. Or say PASS.", names_clone.join(", "));
                    
                    let res = call_provider(&agent_clone, &system, &prompt).await;
                    (agent_clone.id.clone(), res)
                });
            }

            let mut votes: std::collections::HashMap<String, u32> = std::collections::HashMap::new();
            while let Some(res) = set.join_next().await {
                if let Ok((id, res)) = res {
                    if let Some(a) = state.agents.iter_mut().find(|a| a.id == id) {
                        a.is_thinking = false;
                        if let Ok(vote) = res {
                            let vote = vote.trim().to_string();
                            a.vote_target = Some(vote.clone());
                            state.logs.push(format!("🗳️ {} -> {}", a.name, vote));
                            
                            if vote.to_lowercase() != "pass" {
                                *votes.entry(vote).or_insert(0) += 1;
                            }
                        }
                        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                    }
                }
            }

            // Count votes and eliminate if majority
            if let Some((target, count)) = votes.iter().max_by_key(|(_, c)| *c) {
                let majority = (state.alive_agents().len() / 2 + 1) as u32;
                if *count >= majority {
                    for a in &mut state.agents {
                        if a.name.to_lowercase().contains(&target.to_lowercase()) && a.is_alive {
                            let was_monster = a.role == AgentRole::Monster;
                            a.is_alive = false;
                            a.role = AgentRole::Dead;
                            state.last_eliminated = Some(a.name.clone());
                            if was_monster {
                                state.logs.push(format!("⚖️ {} elendi! O CANAVARDI! 🎉", a.name));
                            } else {
                                state.logs.push(format!("⚖️ {} elendi... Masum biriydi. 😢", a.name));
                            }
                            break;
                        }
                    }
                } else {
                    state.logs.push("⚖️ Yeterli çoğunluk sağlanamadı. Kimse elenmedi.".to_string());
                }
            } else {
                state.logs.push("⚖️ Herkes PAS geçti. Kimse elenmedi.".to_string());
            }

            // Next night
            state.day += 1;
            state.last_victim = None;
            state.phase = GamePhase::Night;
            state.logs.push(format!("🌙 GECE {} - Kasaba uykuya dalıyor...", state.day));
        },

        GamePhase::GameOver => {
            // Do nothing, game ended
        }
    }

    // Limit log size
    if state.logs.len() > 100 {
        state.logs.drain(0..20);
    }
}
