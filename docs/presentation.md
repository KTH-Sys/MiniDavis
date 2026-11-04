# MiniDavis presentation materials

Use the [single illustrated LaTeX PDF guide](../output/pdf/MiniDavis-Presentation-Guide.pdf). It contains plain-language explanations, suggested speaker wording, screenshots, architecture and ML diagrams, demo steps, audience questions and evidence limits. It has no timestamps or suggested speaking durations.

## Speakers

| Topic | Presenter |
| --- | --- |
| Frontend | Saurya |
| Backend | Rylee |
| RAG and memories | Ethan |
| Classifier | Gayatri |
| Live demo | Aishani / Saurya |
| Further development | Aishani |

Eric can introduce and close the project as team lead.

## Audience interface

The default screen shows the town, resident goals/supplies/stories, Play/Pause, Next Turn, Reset and Recorded example. Technical tabs, memory sources, classifier testing, seeds, grid, modes and API counters stay behind **Presenter tools**. Close those tools before the demo.

Set up the live mode before presenting, then advance a turn and describe the actual action. A live interaction is not guaranteed. Use **Recorded example** for a reproducible trade and conversation, and explicitly call it a scripted recording. It does not make new AI decisions.

## Before presenting

- Install the model package and follow the root README's startup instructions.
- Use Presenter tools to confirm live AI, semantic memory and classifier setup.
- Verify a real live plan arrives, then close the tools.
- Check Recorded example, Reset and resident selection.
- Rehearse on the actual display and network. Keep this PDF available if the service fails.
- Keep API keys and operator passwords out of slides and the public interface.

## Rebuild the PDF

The editable LaTeX source is [MiniDavis-Presentation-Guide.tex](presentation/MiniDavis-Presentation-Guide.tex). It uses actual app screenshots in `docs/assets/` and native TikZ diagrams. With Tectonic installed:

```bash
sh scripts/build_presentation.sh
```

The output is `output/pdf/MiniDavis-Presentation-Guide.pdf`. Evaluation numbers come from `results/presentation/`; the PDF distinguishes measured results, illustrative diagrams and scripted examples.
