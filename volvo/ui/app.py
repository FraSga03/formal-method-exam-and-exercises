"""Dashboard wiring. All logic lives in handlers.py."""
from typing import get_args

import gradio as gr

from volvo.domain import DEFAULT_ACTIVITY_MODE, ActivityMode
from volvo.mining.discovery import ALGORITHMS
from volvo.ui import handlers

MODES = list(get_args(ActivityMode))
TITLE = "Volvo IT Process Mining"


def refresh_activities(bundle):
    """Repopulates both activity pickers after the loaded log changes."""
    choices = handlers.activity_choices(bundle)
    return gr.Dropdown(choices=choices, value=[]), gr.Dropdown(choices=choices, value=None)


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

        with gr.Tab("Preprocessing"):
            gr.Markdown(
                "Filters return a new log; reload from the Data tab to undo. They "
                "compose in a fixed order: activities, time range, case length, "
                "duplicates, relabelling."
            )
            with gr.Row():
                prep_activities = gr.Dropdown(
                    [], multiselect=True, label="Activities", scale=3
                )
                activity_action = gr.Radio(
                    ["keep", "exclude"], value="keep", label="Chosen activities"
                )
            with gr.Row():
                start_date = gr.Textbox(label="From", placeholder="2012-03-01")
                end_date = gr.Textbox(label="To", placeholder="2012-06-30")
            with gr.Row():
                min_events = gr.Slider(1, 50, value=1, step=1, label="Minimum events per case")
                max_events = gr.Number(label="Maximum events per case", precision=0)
                drop_dupes = gr.Checkbox(label="Drop duplicate events")
            relabelling = gr.Textbox(
                label="Relabelling",
                lines=3,
                placeholder="Accepted+In Progress = Working\nQueued+Awaiting Assignment = Waiting",
                info="One `old = new` per line. Unlisted activities keep their label.",
            )
            prep_button = gr.Button("Apply", variant="primary")
            prep_summary = gr.Markdown()

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

        with gr.Tab("Anomalies"):
            gr.Markdown("Statistical outliers. Every threshold is a modelling choice.")
            with gr.Row():
                length_std = gr.Slider(
                    0.5, 4.0, value=2.0, step=0.1, label="Case length (standard deviations)"
                )
                rare_pct = gr.Slider(
                    0.1, 5.0, value=1.0, step=0.1, label="Rare activity (% of events)"
                )
            with gr.Row():
                wait_hours = gr.Slider(1, 720, value=24, step=1, label="Long wait (hours)")
                min_support = gr.Slider(
                    2, 20, value=2, step=1, label="Rare transition (fewer than N)"
                )
            anomaly_button = gr.Button("Detect", variant="primary")
            anomaly_text = gr.Markdown()
            with gr.Row():
                length_table = gr.Dataframe(label="Unusual case lengths")
                rare_table = gr.Dataframe(label="Rare activities")
            with gr.Row():
                wait_table = gr.Dataframe(label="Long waits")
                transition_table = gr.Dataframe(label="Rare transitions")
            anomaly_button.click(
                handlers.run_anomalies,
                inputs=[bundle, length_std, rare_pct, wait_hours, min_support],
                outputs=[
                    anomaly_text, length_table, rare_table, wait_table, transition_table,
                ],
            )

        with gr.Tab("Prediction"):
            gr.Markdown(
                "A first-order Markov model over the loaded log: the next activity "
                "depends on the current one alone, so a long walk is indicative, not a "
                "forecast."
            )
            predict_activity = gr.Dropdown([], label="Current activity")
            with gr.Row():
                top_k = gr.Slider(1, 10, value=3, step=1, label="Successors shown")
                walk_length = gr.Slider(2, 20, value=5, step=1, label="Sequence length")
            with gr.Row():
                next_button = gr.Button("Predict next", variant="primary")
                sequence_button = gr.Button("Predict sequence")
            predict_text = gr.Markdown()
            predict_table = gr.Dataframe(label="Successor probabilities")
            next_button.click(
                handlers.predict_next,
                inputs=[bundle, predict_activity, top_k],
                outputs=[predict_text, predict_table],
            )
            sequence_button.click(
                handlers.predict_sequence,
                inputs=[bundle, predict_activity, walk_length],
                outputs=[predict_text],
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

        activity_pickers = [prep_activities, predict_activity]
        load_outputs = [bundle, data_summary, data_table, data_plot]
        prep_inputs = [
            bundle, prep_activities, activity_action, start_date, end_date,
            min_events, max_events, drop_dupes, relabelling,
        ]

        load_button.click(handlers.load_log, [log_name, mode], load_outputs).then(
            refresh_activities, bundle, activity_pickers
        )
        prep_button.click(
            handlers.apply_preprocessing, prep_inputs, [bundle, prep_summary]
        ).then(refresh_activities, bundle, activity_pickers)
        demo.load(handlers.load_log, [log_name, mode], load_outputs).then(
            refresh_activities, bundle, activity_pickers
        )

    return demo
