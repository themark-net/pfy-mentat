#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::Value;
use std::path::PathBuf;
use std::process::Command;

fn repo_root() -> PathBuf {
    if let Ok(r) = std::env::var("PFY_ROOT") {
        return PathBuf::from(r);
    }
    if let Ok(exe) = std::env::current_exe() {
        let mut p = exe;
        for _ in 0..12 {
            match p.parent() {
                Some(parent) => {
                    p = parent.to_path_buf();
                    if p.join("scripts").join("pfy").exists() {
                        return p;
                    }
                }
                None => break,
            }
        }
    }
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
}

fn run_board(args: &["&str"]) -> Result<Value, String> {
