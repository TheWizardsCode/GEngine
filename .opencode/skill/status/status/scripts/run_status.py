#!/usr/bin/env python3
"""
Run status helpers: call `waif in-progress --json` or `bd show <id> --json`, parse and pretty-print summaries.
This script is intended to be used by the status skill to run commands reliably and return JSON output or human-friendly summaries.
"""

import sys
import json
import subprocess


def run_cmd(cmd):
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True, text=True
        )
        return out
    except subprocess.CalledProcessError as e:
        print(
            json.dumps(
                {
                    "error": True,
                    "cmd": cmd,
                    "returncode": e.returncode,
                    "output": e.output,
                }
            )
        )
        sys.exit(1)


def main(argv):
    if len(argv) < 2:
        print(
            json.dumps(
                {"error": True, "message": "usage: run_status.py [waif|bd] [args...]"}
            )
        )
        sys.exit(2)
    tool = argv[1]
    if tool == "waif":
        cmd = "waif in-progress --json"
    elif tool == "bd":
        if len(argv) < 3:
            print(json.dumps({"error": True, "message": "missing bead id for bd"}))
            sys.exit(2)
        bead = argv[2]
        cmd = f"bd show {bead} --json"
    else:
        print(json.dumps({"error": True, "message": f"unknown tool {tool}"}))
        sys.exit(2)
    out = run_cmd(cmd)
    try:
        parsed = json.loads(out)
    except json.JSONDecodeError:
        print(
            json.dumps({"error": True, "message": "failed to parse json", "raw": out})
        )
        sys.exit(1)

    # If called for waif, produce a short human summary
    if tool == "waif":
        summary = summarize_waif(parsed)
        print(json.dumps({"summary": summary, "raw": parsed}))
        return

    # If called for bd, produce a formatted bead detail
    if tool == "bd":
        detail = format_bead(parsed)
        print(json.dumps({"detail": detail, "raw": parsed}))
        return


def summarize_waif(data):
    """
    Produce a concise summary from waif in-progress JSON.
    Expected structure: list of beads or dict with items; handle common variants gracefully.
    """
    # Normalize to a list of items
    items = []
    if isinstance(data, dict):
        # try common keys
        if "items" in data and isinstance(data["items"], list):
            items = data["items"]
        elif "beads" in data and isinstance(data["beads"], list):
            items = data["beads"]
        else:
            # maybe the data itself is the bead dict
            items = [data]
    elif isinstance(data, list):
        items = data

    total = len(items)
    by_priority = {}
    blocked = []
    missing_assignee = []
    top_items = []

    for it in items:
        title = it.get("title") or it.get("name") or it.get("summary") or it.get("id")
        bead_id = it.get("id") or it.get("bead_id") or it.get("key")
        assignee = it.get("assignee") or it.get("owner")
        status = it.get("status")
        priority = it.get("priority") or it.get("prio") or "medium"
        if not assignee:
            missing_assignee.append(bead_id or title)
        if status and status.lower() == "blocked":
            blocked.append(bead_id or title)
        by_priority.setdefault(priority, 0)
        by_priority[priority] += 1
        top_items.append(
            {"id": bead_id, "title": title, "assignee": assignee, "priority": priority}
        )

    # sort top_items by priority if possible
    def prio_val(p):
        mapping = {"critical": 0, "high": 1, "medium": 2, "low": 3, "4": 3}
        return mapping.get(str(p).lower(), 2)

    top_items_sorted = sorted(top_items, key=lambda x: prio_val(x.get("priority")))
    top_lines = []
    for itm in top_items_sorted[:5]:
        line = f"{itm.get('id') or ''} - {itm.get('title') or ''}"
        if itm.get("assignee"):
            line += f" (assignee: {itm.get('assignee')})"
        if itm.get("priority"):
            line += f" [priority: {itm.get('priority')}]"
        top_lines.append(line)

    suggestion = None
    if top_items_sorted:
        first = top_items_sorted[0]
        suggestion = f"Review {first.get('id') or first.get('title')} assigned to {first.get('assignee') or 'unassigned'}."

    summary = {
        "total_in_progress": total,
        "by_priority": by_priority,
        "blocked_items": blocked,
        "missing_assignees": missing_assignee,
        "top_items": top_lines,
        "suggestion": suggestion,
    }
    return summary


def format_bead(data):
    """
    Format bd show JSON into a human-friendly dictionary of fields.
    Expect a dict representing a bead.
    """
    # If the input is a list with single item, use it
    if isinstance(data, list) and len(data) == 1:
        data = data[0]

    bead = {}
    bead["id"] = data.get("id") or data.get("key") or data.get("bead_id")
    bead["title"] = data.get("title") or data.get("name")
    bead["status"] = data.get("status")
    bead["assignee"] = data.get("assignee") or data.get("owner")
    bead["priority"] = data.get("priority") or data.get("prio")
    bead["description"] = data.get("description") or data.get("summary")
    bead["blockers"] = data.get("blockers") or data.get("blocked_by") or []
    bead["dependencies"] = data.get("dependencies") or data.get("deps") or []
    bead["comments_count"] = None
    if isinstance(data.get("comments"), list):
        bead["comments_count"] = len(data.get("comments"))
    # capture urls or links
    bead["links"] = data.get("links") or data.get("url") or data.get("web_url")

    # Create a human-friendly string summary
    lines = []
    lines.append(f"{bead.get('id') or ''}: {bead.get('title') or ''}")
    if bead.get("status"):
        lines.append(f"Status: {bead.get('status')}")
    if bead.get("assignee"):
        lines.append(f"Assignee: {bead.get('assignee')}")
    if bead.get("priority"):
        lines.append(f"Priority: {bead.get('priority')}")
    if bead.get("description"):
        desc = bead.get("description").strip()
        if len(desc) > 300:
            desc_preview = desc[:300] + "..."
        else:
            desc_preview = desc
        lines.append(f"Description: {desc_preview}")
    if bead.get("blockers"):
        lines.append(f"Blockers: {bead.get('blockers')}")
    if bead.get("dependencies"):
        lines.append(f"Dependencies: {bead.get('dependencies')}")
    if bead.get("comments_count") is not None:
        lines.append(f"Comments: {bead.get('comments_count')}")
    if bead.get("links"):
        lines.append(f"Links: {bead.get('links')}")

    bead["human_summary"] = "\n".join(lines)
    return bead


if __name__ == "__main__":
    main(sys.argv)
