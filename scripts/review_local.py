#!/usr/bin/env python3
"""
Local CLI Review & Approval Sandbox for Content Strategist Agent.

Interactive terminal dashboard to review, edit, approve, or discard content
queued in state/ without needing webhooks or third-party apps.

Features:
- Browse pending Module 1 outputs and Module 2 Radar cards
- Inline editor to tweak hooks, body text, or captions
- Export pipeline: move approved content to state/approved/ as Markdown/JSON
- Keyboard-driven UI with color coding
"""

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ANSI Color Codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    
    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    
    @staticmethod
    def strip(text: str) -> str:
        """Remove ANSI codes from text."""
        return re.sub(r'\033\[[0-9;]*m', '', text)


class ReviewSandbox:
    def __init__(self, state_dir: Path = Path("state"), approved_dir: Path = Path("state/approved")):
        self.state_dir = state_dir
        self.approved_dir = approved_dir
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.pending_module1: list[dict] = []
        self.pending_module2: list[dict] = []
        self.current_view = "main"  # main, module1, module2, editor, export
        self.selected_index = 0
        self.scroll_offset = 0
        self.terminal_height = 24
        self.terminal_width = 80
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_terminal_size(self):
        try:
            import shutil
            size = shutil.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines
        except Exception:
            pass
    
    def print_header(self, title: str, subtitle: str = ""):
        self.clear_screen()
        self.get_terminal_size()
        width = self.terminal_width
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * width}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  {title.center(width - 4)}  {Colors.RESET}")
        if subtitle:
            print(f"{Colors.DIM}  {subtitle.center(width - 4)}  {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * width}{Colors.RESET}")
        print()
    
    def print_footer(self, controls: list[str]):
        print()
        print(f"{Colors.GRAY}{'─' * self.terminal_width}{Colors.RESET}")
        print(f"{Colors.DIM}  {'  |  '.join(controls)}{Colors.RESET}")
    
    def truncate(self, text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
    
    def wrap_text(self, text: str, width: int, indent: int = 0) -> list[str]:
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append("")
                continue
            wrapped = textwrap.wrap(paragraph, width=width - indent, 
                                   initial_indent=" " * indent, 
                                   subsequent_indent=" " * indent)
            lines.extend(wrapped if wrapped else [" " * indent + paragraph])
        return lines


# ============================================================================
# DATA LOADING
# ============================================================================

    def load_pending(self):
        """Load all pending content from state/ directory."""
        self.pending_module1 = []
        self.pending_module2 = []
        
        # Module 1: pipeline outputs
        for file in sorted(self.state_dir.glob("*_pipeline_result.md")):
            try:
                content = file.read_text(encoding="utf-8")
                meta = self.parse_pipeline_markdown(content, file.name)
                meta["_source_file"] = str(file)
                meta["_type"] = "module1"
                self.pending_module1.append(meta)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        # Module 2: radar shortlists
        for file in sorted(self.state_dir.glob("shortlist_*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                for item in items:
                    item["_source_file"] = str(file)
                    item["_type"] = "module2"
                    self.pending_module2.append(item)
            except Exception as e:
                print(f"Error loading {file}: {e}")
    
    def parse_pipeline_markdown(self, content: str, filename: str) -> dict:
        """Parse Module 1 pipeline markdown output into structured data."""
        meta = {
            "filename": filename,
            "timestamp": filename.split("_")[0] if "_" in filename else "",
            "hooks": [],
            "script_rows": [],
            "captions": {},
            "raw_content": content
        }
        
        # Extract hooks
        hook_section = re.search(r"## 3\. FIVE HIGH-IMPACT HOOKS.*?\n((?:.*\n)*?)(?:\n## |\Z)", content)
        if hook_section:
            table = hook_section.group(1)
            for line in table.split('\n'):
                if '|' in line and '**' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        hook_type = parts[1].replace('**', '').strip()
                        hook_text = parts[2].strip()
                        meta["hooks"].append({"type": hook_type, "text": hook_text})
        
        # Extract script rows
        script_section = re.search(r"## 4\. VIDEO SCRIPT \+ EDIT GUIDE.*?\n((?:.*\n)*?)(?:\n## |\Z)", content)
        if script_section:
            table = script_section.group(1)
            for line in table.split('\n'):
                if '|' in line and not line.strip().startswith('|---'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 6:
                        meta["script_rows"].append({
                            "time": parts[1],
                            "voiceover": parts[2],
                            "broll": parts[3],
                            "overlay": parts[4],
                            "sfx": parts[5]
                        })
        
        # Extract captions
        caption_sections = re.findall(r"### (.*?) / Reels / TikTok\n\n```\n(.*?)\n```", content, re.DOTALL)
        for platform, caption in caption_sections:
            meta["captions"][platform.strip().lower()] = caption.strip()
        
        return meta


# ============================================================================
# MAIN MENU
# ============================================================================

    def run_main_menu(self):
        self.load_pending()
        while True:
            self.print_header(
                "CONTENT STRATEGIST — REVIEW SANDBOX",
                f"Module 1: {len(self.pending_module1)} pending  |  Module 2: {len(self.pending_module2)} pending"
            )
            
            print(f"  {Colors.BOLD}1.{Colors.RESET} Module 1 Pipeline Outputs ({len(self.pending_module1)})")
            print(f"  {Colors.BOLD}2.{Colors.RESET} Module 2 Radar Cards ({len(self.pending_module2)})")
            print(f"  {Colors.BOLD}3.{Colors.RESET} Approved Content ({self.count_approved()})")
            print(f"  {Colors.BOLD}4.{Colors.RESET} Export Approved to JSON/Markdown")
            print(f"  {Colors.BOLD}5.{Colors.RESET} Settings")
            print()
            print(f"  {Colors.BOLD}q.{Colors.RESET} Quit")
            
            choice = input(f"\n  {Colors.CYAN}Select option: {Colors.RESET}").strip().lower()
            
            if choice == '1':
                self.run_module1_browser()
            elif choice == '2':
                self.run_module2_browser()
            elif choice == '3':
                self.run_approved_browser()
            elif choice == '4':
                self.run_export()
            elif choice == '5':
                self.run_settings()
            elif choice in ('q', 'quit', 'exit'):
                break
    
    def count_approved(self) -> int:
        return len(list(self.approved_dir.glob("*")))


# ============================================================================
# MODULE 1 BROWSER
# ============================================================================

    def run_module1_browser(self):
        self.selected_index = 0
        self.scroll_offset = 0
        
        while True:
            self.print_header(
                "MODULE 1 — PIPELINE OUTPUTS",
                f"{len(self.pending_module1)} items  |  ↑/↓ navigate  |  Enter: view  |  e: edit  |  a: approve  |  d: discard  |  Esc/q: back"
            )
            
            if not self.pending_module1:
                print(f"  {Colors.YELLOW}No pending Module 1 outputs.{Colors.RESET}")
                print(f"  Run Module 1 pipeline to generate content.")
                input(f"\n  {Colors.DIM}Press Enter to return...{Colors.RESET}")
                return
            
            # Calculate visible items
            visible = self.terminal_height - 10
            start = max(0, min(self.scroll_offset, len(self.pending_module1) - visible))
            end = min(start + visible, len(self.pending_module1))
            
            for i in range(start, end):
                item = self.pending_module1[i]
                prefix = f"{Colors.BG_BLUE}{Colors.WHITE} ► {Colors.RESET} " if i == self.selected_index else "   "
                
                timestamp = item.get("timestamp", "unknown")
                hook_count = len(item.get("hooks", []))
                caption_count = len(item.get("captions", {}))
                
                # First hook preview
                first_hook = item.get("hooks", [{}])[0].get("text", "No hooks") if item.get("hooks") else "No hooks"
                first_hook = self.truncate(first_hook, 50)
                
                status = f"{Colors.GREEN}✓{Colors.RESET}" if hook_count == 5 else f"{Colors.YELLOW}⚠{Colors.RESET}"
                
                print(f"{prefix}{Colors.BOLD}{timestamp}{Colors.RESET}  {status}  Hooks: {hook_count}  Captions: {caption_count}")
                print(f"       {Colors.DIM}{first_hook}{Colors.RESET}")
            
            # Scroll indicators
            if start > 0:
                print(f"  {Colors.DIM}▲ {start} more above{Colors.RESET}")
            if end < len(self.pending_module1):
                print(f"  {Colors.DIM}▼ {len(self.pending_module1) - end} more below{Colors.RESET}")
            
            self.print_footer(["↑/↓ Navigate", "Enter View", "e Edit", "a Approve", "d Discard", "q Back"])
            
            key = self.get_key()
            if key == 'UP':
                self.selected_index = max(0, self.selected_index - 1)
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
            elif key == 'DOWN':
                self.selected_index = min(len(self.pending_module1) - 1, self.selected_index + 1)
                if self.selected_index >= self.scroll_offset + visible:
                    self.scroll_offset = self.selected_index - visible + 1
            elif key == 'ENTER':
                self.view_module1_item(self.pending_module1[self.selected_index])
            elif key == 'e':
                self.edit_module1_item(self.pending_module1[self.selected_index])
            elif key == 'a':
                self.approve_module1_item(self.pending_module1[self.selected_index])
            elif key == 'd':
                self.discard_module1_item(self.pending_module1[self.selected_index])
            elif key in ('q', 'ESC'):
                return
    
    def view_module1_item(self, item: dict):
        while True:
            self.print_header(
                f"MODULE 1 — {item.get('timestamp', 'unknown')}",
                f"Hooks: {len(item.get('hooks', []))}  |  Script rows: {len(item.get('script_rows', []))}  |  Captions: {len(item.get('captions', {}))}"
            )
            
            # Hooks
            print(f"  {Colors.BOLD}HOOKS:{Colors.RESET}")
            for i, hook in enumerate(item.get("hooks", []), 1):
                print(f"    {Colors.CYAN}{i}.{Colors.RESET} [{hook.get('type', 'unknown')}] {hook.get('text', '')}")
            
            # Script rows (first 3)
            print(f"\n  {Colors.BOLD}SCRIPT ROWS (first 3):{Colors.RESET}")
            for row in item.get("script_rows", [])[:3]:
                print(f"    {Colors.CYAN}{row['time']}{Colors.RESET} | {self.truncate(row['voiceover'], 60)}")
                print(f"       Overlay: {self.truncate(row['overlay'], 60)}")
            
            # Captions summary
            print(f"\n  {Colors.BOLD}CAPTIONS:{Colors.RESET}")
            for platform, caption in item.get("captions", {}).items():
                chars = len(caption)
                tags = len(re.findall(r'#\w+', caption))
                print(f"    {Colors.MAGENTA}{platform}{Colors.RESET}: {chars} chars, {tags} hashtags")
            
            self.print_footer(["Enter/e Edit", "a Approve", "d Discard", "q Back"])
            
            key = self.get_key()
            if key in ('e', 'ENTER'):
                self.edit_module1_item(item)
                break
            elif key == 'a':
                self.approve_module1_item(item)
                break
            elif key == 'd':
                self.discard_module1_item(item)
                break
            elif key in ('q', 'ESC'):
                break
    
    def edit_module1_item(self, item: dict):
        """Inline editor for Module 1 item."""
        self.print_header("EDIT MODULE 1 ITEM", f"Editing: {item.get('timestamp', 'unknown')}")
        
        print(f"  {Colors.BOLD}Current Hooks:{Colors.RESET}")
        for i, hook in enumerate(item.get("hooks", []), 1):
            print(f"    {i}. [{hook.get('type')}] {hook.get('text')}")
        
        print(f"\n  {Colors.DIM}Edit hook text (press Enter to keep current, 'del' to delete, 'new' to add):{Colors.RESET}")
        
        new_hooks = []
        for i, hook in enumerate(item.get("hooks", []), 1):
            current = hook.get("text", "")
            print(f"\n  Hook {i} [{hook.get('type')}]")
            new_text = input(f"  > {Colors.CYAN}{current}{Colors.RESET}\n  > ").strip()
            
            if new_text.lower() == 'del':
                print(f"  {Colors.RED}Deleted.{Colors.RESET}")
                continue
            elif new_text.lower() == 'new':
                htype = input(f"  Hook type: ").strip() or "custom"
                htext = input(f"  Hook text: ").strip()
                if htext:
                    new_hooks.append({"type": htype, "text": htext})
                continue
            elif new_text:
                new_hooks.append({"type": hook.get("type", "custom"), "text": new_text})
            else:
                new_hooks.append(hook)
        
        # Update and save
        if new_hooks != item.get("hooks", []):
            item["hooks"] = new_hooks
            self.save_module1_item(item)
            print(f"\n  {Colors.GREEN}✓ Hooks updated!{Colors.RESET}")
        
        input(f"\n  {Colors.DIM}Press Enter to continue...{Colors.RESET}")
    
    def approve_module1_item(self, item: dict):
        """Move Module 1 item to approved."""
        dest = self.approved_dir / f"module1_{item.get('timestamp', 'unknown')}.md"
        shutil.copy2(item["_source_file"], dest)
        
        # Also save structured JSON
        json_dest = self.approved_dir / f"module1_{item.get('timestamp', 'unknown')}.json"
        export_data = {
            "type": "module1",
            "approved_at": datetime.now().isoformat(),
            "hooks": item.get("hooks", []),
            "script_rows": item.get("script_rows", []),
            "captions": item.get("captions", {}),
            "source_file": item["_source_file"]
        }
        json_dest.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # Remove from pending
        self.pending_module1 = [i for i in self.pending_module1 if i.get("_source_file") != item["_source_file"]]
        os.remove(item["_source_file"])
        
        print(f"  {Colors.GREEN}✓ Approved and moved to {dest}{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def discard_module1_item(self, item: dict):
        """Discard Module 1 item."""
        confirm = input(f"  {Colors.RED}Discard this item? (y/N): {Colors.RESET}").strip().lower()
        if confirm == 'y':
            os.remove(item["_source_file"])
            self.pending_module1 = [i for i in self.pending_module1 if i.get("_source_file") != item["_source_file"]]
            print(f"  {Colors.RED}Discarded.{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def save_module1_item(self, item: dict):
        """Save edited Module 1 item back to markdown."""
        content = item.get("raw_content", "")
        
        # Update hooks in content
        hook_lines = []
        for hook in item.get("hooks", []):
            hook_lines.append(f"| **{hook.get('type', '').title()}** | {hook.get('text', '')} | instagram, linkedin, twitter |")
        
        # Replace hooks section
        new_hooks_md = "\n| Type | Hook | Platform Fit |\n|------|------|--------------|\n" + "\n".join(hook_lines) + "\n"
        content = re.sub(
            r"(## 3\. FIVE HIGH-IMPACT HOOKS.*?\n\| Type \| Hook \| Platform Fit \|\n\|------\|------\|--------------\|)(.*?)(\n\|---|\n## )",
            r"\1" + new_hooks_md + r"\3",
            content,
            flags=re.DOTALL
        )
        
        Path(item["_source_file"]).write_text(content, encoding="utf-8")


# ============================================================================
# MODULE 2 BROWSER
# ============================================================================

    def run_module2_browser(self):
        self.selected_index = 0
        self.scroll_offset = 0
        
        while True:
            self.print_header(
                "MODULE 2 — RADAR CARDS",
                f"{len(self.pending_module2)} items  |  ↑/↓ navigate  |  Enter: view  |  e: edit  |  a: approve  |  d: discard  |  Esc/q: back"
            )
            
            if not self.pending_module2:
                print(f"  {Colors.YELLOW}No pending Module 2 radar cards.{Colors.RESET}")
                print(f"  Run Module 2 radar to generate cards.")
                input(f"\n  {Colors.DIM}Press Enter to return...{Colors.RESET}")
                return
            
            visible = self.terminal_height - 10
            start = max(0, min(self.scroll_offset, len(self.pending_module2) - visible))
            end = min(start + visible, len(self.pending_module2))
            
            for i in range(start, end):
                item = self.pending_module2[i]
                prefix = f"{Colors.BG_BLUE}{Colors.WHITE} ► {Colors.RESET} " if i == self.selected_index else "   "
                
                item_id = item.get("item_id", "unknown")
                title = self.truncate(item.get("title", "No title"), 55)
                score = item.get("score", 0)
                source = item.get("source", "unknown")
                angle = item.get("suggested_angle", "unknown")
                
                score_color = Colors.GREEN if score >= 0.8 else Colors.YELLOW if score >= 0.6 else Colors.RED
                
                print(f"{prefix}{Colors.BOLD}{item_id}{Colors.RESET}  {score_color}{score:.0%}{Colors.RESET}  {Colors.MAGENTA}{source}{Colors.RESET}  {Colors.DIM}{angle}{Colors.RESET}")
                print(f"       {Colors.WHITE}{title}{Colors.RESET}")
            
            if start > 0:
                print(f"  {Colors.DIM}▲ {start} more above{Colors.RESET}")
            if end < len(self.pending_module2):
                print(f"  {Colors.DIM}▼ {len(self.pending_module2) - end} more below{Colors.RESET}")
            
            self.print_footer(["↑/↓ Navigate", "Enter View", "e Edit", "a Approve", "d Discard", "q Back"])
            
            key = self.get_key()
            if key == 'UP':
                self.selected_index = max(0, self.selected_index - 1)
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
            elif key == 'DOWN':
                self.selected_index = min(len(self.pending_module2) - 1, self.selected_index + 1)
                if self.selected_index >= self.scroll_offset + visible:
                    self.scroll_offset = self.selected_index - visible + 1
            elif key == 'ENTER':
                self.view_module2_item(self.pending_module2[self.selected_index])
            elif key == 'e':
                self.edit_module2_item(self.pending_module2[self.selected_index])
            elif key == 'a':
                self.approve_module2_item(self.pending_module2[self.selected_index])
            elif key == 'd':
                self.discard_module2_item(self.pending_module2[self.selected_index])
            elif key in ('q', 'ESC'):
                return
    
    def view_module2_item(self, item: dict):
        while True:
            self.print_header(
                f"MODULE 2 — {item.get('item_id', 'unknown')}",
                f"Score: {item.get('score', 0):.0%}  |  Source: {item.get('source', 'unknown')}  |  Angle: {item.get('suggested_angle', 'unknown')}"
            )
            
            print(f"  {Colors.BOLD}Title:{Colors.RESET} {item.get('title', 'No title')}")
            print(f"  {Colors.BOLD}Source:{Colors.RESET} {item.get('source', 'unknown')}  |  {item.get('source_url', '')}")
            print(f"  {Colors.BOLD}Published:{Colors.RESET} {item.get('published_at', 'unknown')}")
            
            print(f"\n  {Colors.BOLD}Executive Summary:{Colors.RESET}")
            for line in self.wrap_text(item.get("executive_summary", ""), self.terminal_width - 4, 4):
                print(f"  {line}")
            
            print(f"\n  {Colors.BOLD}Key Insight:{Colors.RESET}")
            for line in self.wrap_text(item.get("key_insight", ""), self.terminal_width - 4, 4):
                print(f"  {line}")
            
            print(f"\n  {Colors.BOLD}Draft Post:{Colors.RESET}")
            draft = item.get("draft_post", "")
            for line in self.wrap_text(draft, self.terminal_width - 4, 4):
                print(f"  {line}")
            
            print(f"\n  {Colors.BOLD}Keywords:{Colors.RESET} {', '.join(item.get('keywords_matched', []))}")
            
            self.print_footer(["Enter/e Edit", "a Approve", "d Discard", "q Back"])
            
            key = self.get_key()
            if key in ('e', 'ENTER'):
                self.edit_module2_item(item)
                break
            elif key == 'a':
                self.approve_module2_item(item)
                break
            elif key == 'd':
                self.discard_module2_item(item)
                break
            elif key in ('q', 'ESC'):
                break
    
    def edit_module2_item(self, item: dict):
        self.print_header("EDIT MODULE 2 CARD", f"Editing: {item.get('item_id', 'unknown')}")
        
        # Edit executive summary
        print(f"  {Colors.BOLD}Executive Summary:{Colors.RESET}")
        current = item.get("executive_summary", "")
        print(f"  Current: {self.truncate(current, 80)}")
        new = input(f"  > ").strip()
        if new:
            item["executive_summary"] = new
        
        # Edit key insight
        print(f"\n  {Colors.BOLD}Key Insight:{Colors.RESET}")
        current = item.get("key_insight", "")
        print(f"  Current: {self.truncate(current, 80)}")
        new = input(f"  > ").strip()
        if new:
            item["key_insight"] = new
        
        # Edit draft post
        print(f"\n  {Colors.BOLD}Draft Post:{Colors.RESET}")
        current = item.get("draft_post", "")
        print(f"  Current: {self.truncate(current, 80)}")
        new = input(f"  > ").strip()
        if new:
            item["draft_post"] = new
        
        # Edit angle
        print(f"\n  {Colors.BOLD}Suggested Angle:{Colors.RESET}")
        angles = ["Contrarian", "Educational", "Case Study", "Prediction", "Framework"]
        current = item.get("suggested_angle", "Contrarian")
        print(f"  Current: {current}")
        print(f"  Options: {', '.join(angles)}")
        new = input(f"  > ").strip()
        if new in angles:
            item["suggested_angle"] = new
        
        # Save back to shortlist JSON
        self.save_module2_item(item)
        print(f"\n  {Colors.GREEN}✓ Card updated!{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def save_module2_item(self, item: dict):
        source_file = Path(item.get("_source_file", ""))
        if not source_file.exists():
            return
        
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            
            # Find and update
            for i, existing in enumerate(items):
                if existing.get("item_id") == item.get("item_id"):
                    items[i] = {k: v for k, v in item.items() if not k.startswith("_")}
                    break
            
            with open(source_file, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving: {e}")
    
    def approve_module2_item(self, item: dict):
        item_id = item.get("item_id", "unknown")
        dest = self.approved_dir / f"module2_{item_id}.json"
        
        export_data = {
            "type": "module2",
            "approved_at": datetime.now().isoformat(),
            "item_id": item_id,
            "title": item.get("title"),
            "source": item.get("source"),
            "source_url": item.get("source_url"),
            "score": item.get("score"),
            "executive_summary": item.get("executive_summary"),
            "key_insight": item.get("key_insight"),
            "suggested_angle": item.get("suggested_angle"),
            "draft_post": item.get("draft_post"),
            "platform": item.get("platform"),
            "tone_id": item.get("tone_id"),
            "keywords_matched": item.get("keywords_matched", [])
        }
        
        dest.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # Also create Markdown version for easy copy-paste
        md_dest = self.approved_dir / f"module2_{item_id}.md"
        md_content = f"""# Module 2 Approved — {item_id}

**Title:** {item.get('title', 'No title')}  
**Source:** {item.get('source', 'unknown')}  
**Score:** {item.get('score', 0):.0%}  
**Angle:** {item.get('suggested_angle', 'unknown')}  
**Approved:** {datetime.now().isoformat()}

## Executive Summary
{item.get('executive_summary', '')}

## Key Insight
{item.get('key_insight', '')}

## Draft Post
{item.get('draft_post', '')}

## Metadata
- Keywords: {', '.join(item.get('keywords_matched', []))}
- Platform: {item.get('platform', 'linkedin')}
- Tone: {item.get('tone_id', 'b2b_corporate')}
"""
        md_dest.write_text(md_content, encoding="utf-8")
        
        # Remove from pending
        source_file = Path(item.get("_source_file", ""))
        if source_file.exists():
            # Remove from the shortlist JSON
            try:
                with open(source_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                items = [i for i in items if i.get("item_id") != item_id]
                with open(source_file, "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        
        self.pending_module2 = [i for i in self.pending_module2 if i.get("item_id") != item_id]
        
        print(f"  {Colors.GREEN}✓ Approved and saved to {dest}{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def discard_module2_item(self, item: dict):
        confirm = input(f"  {Colors.RED}Discard this card? (y/N): {Colors.RESET}").strip().lower()
        if confirm == 'y':
            # Remove from shortlist JSON
            source_file = Path(item.get("_source_file", ""))
            if source_file.exists():
                try:
                    with open(source_file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                    items = [i for i in items if i.get("item_id") != item.get("item_id")]
                    with open(source_file, "w", encoding="utf-8") as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            
            self.pending_module2 = [i for i in self.pending_module2 if i.get("item_id") != item.get("item_id")]
            print(f"  {Colors.RED}Discarded.{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")


# ============================================================================
# APPROVED BROWSER
# ============================================================================

    def run_approved_browser(self):
        self.print_header("APPROVED CONTENT", f"{self.count_approved()} approved items")
        
        approved_files = sorted(self.approved_dir.glob("*"))
        if not approved_files:
            print(f"  {Colors.YELLOW}No approved content yet.{Colors.RESET}")
            input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
            return
        
        for f in approved_files:
            rel = f.relative_to(self.approved_dir)
            print(f"  {Colors.CYAN}{rel}{Colors.RESET}")
        
        self.print_footer(["q Back"])
        while True:
            key = self.get_key()
            if key in ('q', 'ESC'):
                break


# ============================================================================
# EXPORT
# ============================================================================

    def run_export(self):
        self.print_header("EXPORT APPROVED CONTENT", "Package approved content for schedulers")
        
        approved_files = sorted(self.approved_dir.glob("*.json"))
        module1_files = [f for f in approved_files if f.name.startswith("module1_")]
        module2_files = [f for f in approved_files if f.name.startswith("module2_")]
        
        print(f"  {Colors.BOLD}Available:{Colors.RESET}")
        print(f"    Module 1: {len(module1_files)} items")
        print(f"    Module 2: {len(module2_files)} items")
        print()
        
        print(f"  {Colors.BOLD}Export Options:{Colors.RESET}")
        print(f"    {Colors.BOLD}1.{Colors.RESET} Export all as single JSON (for Notion/Buffer API)")
        print(f"    {Colors.BOLD}2.{Colors.RESET} Export all as Markdown files (for Hootsuite/Buffer)")
        print(f"    {Colors.BOLD}3.{Colors.RESET} Export Module 1 only")
        print(f"    {Colors.BOLD}4.{Colors.RESET} Export Module 2 only")
        print(f"    {Colors.BOLD}5.{Colors.RESET} Custom selection")
        
        choice = input(f"\n  {Colors.CYAN}Select: {Colors.RESET}").strip()
        
        if choice == '1':
            self.export_all_json()
        elif choice == '2':
            self.export_all_markdown()
        elif choice == '3':
            self.export_module1_json()
        elif choice == '4':
            self.export_module2_json()
        elif choice == '5':
            self.export_custom()
    
    def export_all_json(self):
        output = {
            "exported_at": datetime.now().isoformat(),
            "module1": [],
            "module2": []
        }
        
        for f in sorted(self.approved_dir.glob("module1_*.json")):
            output["module1"].append(json.loads(f.read_text(encoding="utf-8")))
        
        for f in sorted(self.approved_dir.glob("module2_*.json")):
            output["module2"].append(json.loads(f.read_text(encoding="utf-8")))
        
        dest = Path(f"export_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        dest.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {Colors.GREEN}✓ Exported to {dest}{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def export_all_markdown(self):
        dest_dir = Path(f"export_md_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for f in sorted(self.approved_dir.glob("*.md")):
            shutil.copy2(f, dest_dir / f.name)
            count += 1
        
        print(f"  {Colors.GREEN}✓ Exported {count} Markdown files to {dest_dir}{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def export_module1_json(self):
        output = {"module1": []}
        for f in sorted(self.approved_dir.glob("module1_*.json")):
            output["module1"].append(json.loads(f.read_text(encoding="utf-8")))
        
        dest = Path(f"export_module1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        dest.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {Colors.GREEN}✓ Exported to {dest}{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def export_module2_json(self):
        output = {"module2": []}
        for f in sorted(self.approved_dir.glob("module2_*.json")):
            output["module2"].append(json.loads(f.read_text(encoding="utf-8")))
        
        dest = Path(f"export_module2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        dest.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {Colors.GREEN}✓ Exported to {dest}{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")
    
    def export_custom(self):
        print(f"  {Colors.YELLOW}Custom selection not yet implemented.{Colors.RESET}")
        input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")


# ============================================================================
# SETTINGS
# ============================================================================

    def run_settings(self):
        self.print_header("SETTINGS")
        print(f"  State directory: {self.state_dir}")
        print(f"  Approved directory: {self.approved_dir}")
        print(f"  Terminal: {self.terminal_width}x{self.terminal_height}")
        print()
        
        print(f"  {Colors.BOLD}1.{Colors.RESET} Change state directory")
        print(f"  {Colors.BOLD}2.{Colors.RESET} Change approved directory")
        print(f"  {Colors.BOLD}3.{Colors.RESET} Reset terminal size detection")
        
        choice = input(f"\n  {Colors.CYAN}Select: {Colors.RESET}").strip()
        
        if choice == '1':
            new = input(f"  New state dir [{self.state_dir}]: ").strip()
            if new:
                self.state_dir = Path(new)
        elif choice == '2':
            new = input(f"  New approved dir [{self.approved_dir}]: ").strip()
            if new:
                self.approved_dir = Path(new)
                self.approved_dir.mkdir(parents=True, exist_ok=True)
        elif choice == '3':
            self.get_terminal_size()
            print(f"  {Colors.GREEN}Terminal size updated: {self.terminal_width}x{self.terminal_height}{Colors.RESET}")
            input(f"\n  {Colors.DIM}Press Enter...{Colors.RESET}")


# ============================================================================
# INPUT HANDLING
# ============================================================================

    def get_key(self) -> str:
        """Get a single keypress, handling arrows and special keys."""
        try:
            import msvcrt
            # Windows
            ch = msvcrt.getch()
            if ch in (b'\xe0', b'\x00'):  # Arrow key prefix
                ch2 = msvcrt.getch()
                if ch2 == b'H': return 'UP'
                if ch2 == b'P': return 'DOWN'
                if ch2 == b'M': return 'RIGHT'
                if ch2 == b'K': return 'LEFT'
            elif ch == b'\r': return 'ENTER'
            elif ch == b'\x1b': return 'ESC'
            elif ch == b'\x03': raise KeyboardInterrupt
            return ch.decode('utf-8', errors='ignore')
        except ImportError:
            # Unix-like
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A': return 'UP'
                        if ch3 == 'B': return 'DOWN'
                        if ch3 == 'C': return 'RIGHT'
                        if ch3 == 'D': return 'LEFT'
                    return 'ESC'
                elif ch == '\r': return 'ENTER'
                elif ch == '\x03': raise KeyboardInterrupt
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main():
    parser = argparse.ArgumentParser(description="Local CLI Review & Approval Sandbox")
    parser.add_argument("--state-dir", default="state", help="State directory path")
    parser.add_argument("--approved-dir", default="state/approved", help="Approved content directory")
    args = parser.parse_args()
    
    sandbox = ReviewSandbox(Path(args.state_dir), Path(args.approved_dir))
    
    try:
        sandbox.run_main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()