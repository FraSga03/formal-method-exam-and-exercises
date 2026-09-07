"""Dashboard wiring. All logic lives in handlers.py."""
import gradio as gr

from volvo.domain import DEFAULT_ACTIVITY_MODE
from volvo.mining.discovery import ALGORITHMS
from volvo.ui import handlers

MODES = ["status", "substatus", "status_substatus"]
TITLE = "Volvo IT Process Mining"


def build() -> gr.Blocks:
    with gr.Blocks(title=TITLE) as demo:
        bundle = gr.State(None)
        gr.Markdown(f"# {TITLE}\nBPI Challenge 2013 — VINST incident and problem logs")

        with gr.Tab("Data"):
            with gr.Row():
                log_name = gr.Dropdown(
                    handlers.available_logs(), label="Log", value=handlers.default_log()
                )
                mode = gr.Radio(MODES, value=DEFAULT_ACTIVITY_MODE, label="Activity label")
                load_button = gr.Button("Load", variant="primary")
            data_summary = gr.Markdown()
            with gr.Row():
                data_table = gr.Dataframe(label="Activity counts")
                data_plot = gr.Plot()
            load_button.click(
                handlers.load_log,
                inputs=[log_name, mode],
                outputs=[bundle, data_summary, data_table, data_plot],
            )

        with gr.Tab("Preprocessing"):
            gr.Markdown("Filters return a new log; reload from the Data tab to undo.")
            with gr.Row():
                min_events = gr.Slider(1, 50, value=1, step=1, label="Minimum events per case")
                drop_dupes = gr.Checkbox(label="Drop duplicate events")
            prep_button = gr.Button("Apply")
            prep_summary = gr.Markdown()
            prep_button.click(
                handlers.apply_preprocessing,
                inputs=[bundle, min_events, drop_dupes],
                outputs=[bundle, prep_summary],
            )

        with gr.Tab("Discovery"):
            with gr.Row():
                algorithm = gr.Dropdown(list(ALGORITHMS), value="inductive", label="Algorithm")
                threshold = gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="Threshold")
                discover_button = gr.Button("Discover", variant="primary")
            discovery_text = gr.Markdown()
            with gr.Row():
                net_image = gr.Image(label="Petri net")
                structure = gr.Dataframe(label="Model structure")
            discover_button.click(
                handlers.run_discovery,
                inputs=[bundle, algorithm, threshold],
                outputs=[net_image, discovery_text, structure],
            )

        with gr.Tab("Conformance"):
            with gr.Row():
                conf_algorithm = gr.Dropdown(list(ALGORITHMS), value="inductive", label="Algorithm")
                method = gr.Radio(["token", "alignment"], value="token", label="Method")
                max_cases = gr.Slider(50, 5000, value=500, step=50, label="Cases sampled")
            with gr.Row():
                conf_button = gr.Button("Evaluate", variant="primary")
                compare_button = gr.Button("Compare all algorithms")
            conf_text = gr.Markdown()
            conf_table = gr.Dataframe()
            conf_button.click(
                handlers.run_conformance,
                inputs=[bundle, conf_algorithm, method, max_cases],
                outputs=[conf_text, conf_table],
            )
            compare_button.click(
                handlers.run_comparison,
                inputs=[bundle, max_cases],
                outputs=[conf_text, conf_table],
            )

        with gr.Tab("LTL"):
            gr.Markdown(
                "Finite-trace LTL. Operators: `G` always, `F` eventually, `X` next, "
                "`U` until, with `!`, `&`, `|`, `->`. Activity names become lowercase "
                "symbols: `Accepted+In Progress` is `accepted_in_progress`."
            )
            with gr.Row():
                preset = gr.Dropdown(handlers.property_choices(), label="Shipped property")
                formula = gr.Textbox(label="Formula", scale=3)
            with gr.Row():
                verify_button = gr.Button("Verify", variant="primary")
                library_button = gr.Button("Verify whole library")
            ltl_text = gr.Markdown()
            ltl_table = gr.Dataframe(label="Counterexamples")
            max_counterexamples = gr.Number(10, visible=False)
            preset.change(handlers.property_formula, inputs=[preset], outputs=[formula])
            verify_button.click(
                handlers.run_ltl,
                inputs=[bundle, formula, max_counterexamples],
                outputs=[ltl_text, ltl_table],
            )
            library_button.click(
                handlers.run_property_library, inputs=[bundle], outputs=[ltl_text, ltl_table]
            )

        with gr.Tab("Analytics"):
            analytics_button = gr.Button("Analyse", variant="primary")
            analytics_text = gr.Markdown()
            analytics_table = gr.Dataframe(label="Waiting time by activity")
            with gr.Row():
                wait_plot = gr.Plot()
                duration_plot = gr.Plot()
            heatmap_plot = gr.Plot()
            analytics_button.click(
                handlers.run_analytics,
                inputs=[bundle],
                outputs=[
                    analytics_text, analytics_table,
                    wait_plot, duration_plot, heatmap_plot,
                ],
            )

        with gr.Tab("Report"):
            with gr.Row():
                report_provider = gr.Dropdown(
                    handlers.provider_choices(),
                    value=handlers.NONE_PROVIDER,
                    label="Narrative provider",
                    info=handlers.provider_help(),
                )
                report_button = gr.Button("Generate", variant="primary")
            report_path = gr.Textbox(label="Saved to", interactive=False)
            report_view = gr.Markdown()
            report_button.click(
                handlers.generate_report,
                inputs=[bundle, report_provider],
                outputs=[report_view, report_path],
            )

        with gr.Tab("Assistant"):
            gr.Markdown(
                "Answers are grounded in the loaded log — the model is given the "
                "measured figures and told not to invent any. It still cannot see "
                "anything the analysis did not compute."
            )
            assistant_provider = gr.Dropdown(
                handlers.provider_choices(),
                value=handlers.NONE_PROVIDER,
                label="Provider",
                info=handlers.provider_help(),
            )
            # gradio 6 dropped Chatbot(type=...); the messages format is the default
            transcript = gr.Chatbot(label="Conversation", height=420, resizable=True)
            question = gr.Textbox(
                label="", placeholder="Ask about the loaded log, then press Enter",
                submit_btn=True,
            )
            gr.Examples(handlers.SUGGESTED_QUESTIONS, inputs=question, label="Try")
            clear_button = gr.Button("Clear conversation")

            question.submit(
                handlers.chat,
                inputs=[bundle, question, transcript, assistant_provider],
                outputs=[transcript, question],
            )
            clear_button.click(lambda: [], outputs=[transcript])

        demo.load(
            handlers.load_log,
            inputs=[log_name, mode],
            outputs=[bundle, data_summary, data_table, data_plot],
        )

    return demo
