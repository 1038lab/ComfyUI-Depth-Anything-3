import { app } from "/scripts/app.js";

async function setupLocale() {
    const lang = (
        (window.localStorage && localStorage.getItem("AGL.Locale")) ||
        (app.ui?.settings?.getSettingValue && app.ui.settings.getSettingValue("Comfy.Locale")) ||
        navigator.language ||
        "en"
    ).toLowerCase();

    if (!lang.startsWith("zh")) return;

    try {
        const resp = await fetch(new URL("../locales/zh-CN.json", import.meta.url));
        if (!resp.ok) return;
        const translations = await resp.json();

        app.registerExtension({
            name: "1038lab.DA3.locale",
            nodeCreated(node) {
                const nclass = node.comfyClass;
                const data = translations[nclass];
                if (!data) return;

                if (data.title) {
                    node.title = data.title;
                }

                if (data.inputs && node.inputs) {
                    node.inputs.forEach((inp) => {
                        if (data.inputs[inp.name]) {
                            inp.label = data.inputs[inp.name];
                        }
                    });
                }

                if (data.widgets && node.widgets) {
                    node.widgets.forEach((w) => {
                        if (data.inputs && data.inputs[w.name]) {
                            w.label = data.inputs[w.name];
                        }
                    });
                }
            },
        });
    } catch (e) {
        // Fallback silently to English default
    }
}

setupLocale();
