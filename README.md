# context-packer

![tests](https://github.com/cliffordscott0909/context-packer/actions/workflows/tests.yml/badge.svg)

Pack a project's source files into a single prompt for an AI coding assistant, with a rough token estimate and an optional budget.

```bash
python context_packer.py ./my-project -e .py -e .md -m 20000 -o prompt.txt
```

- Skips `.git`, `node_modules`, virtualenvs, build output, images and binary files
- `-e/--ext` limits to given extensions; `-m/--max-tokens` skips files that would exceed the budget
- `-g/--gitignore` also honors simple patterns from the root `.gitignore`; `-f markdown` outputs fenced code blocks
- Token estimate is ~4 characters per token (approximate)

Run tests: `pip install pytest && pytest`

Inspired by the context-engineering ideas in [coleam00/context-engineering-intro](https://github.com/coleam00/context-engineering-intro).
