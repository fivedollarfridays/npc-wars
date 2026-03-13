## Bot Submission

**Bot Name**: <!-- e.g. TurboGoose -->
**Emoji**: <!-- unique single emoji, e.g. 🦅 -->
**Author**: <!-- your GitHub username -->

### Strategy Description
<!-- Briefly describe your bot's strategy (1-3 sentences) -->

### Checklist
- [ ] Bot file is in `bots/` and named `<something>.py` (no `template` prefix, no `_` prefix)
- [ ] `BOT_NAME`, `BOT_EMOJI`, and `BOT_AUTHOR` are set
- [ ] `decide(state)` returns a valid action tuple every call
- [ ] Bot does not use external network calls or file I/O
- [ ] `python scripts/validate_bot.py bots/<your_bot>.py` passes locally
- [ ] Emoji is unique (not used by any existing bot)
