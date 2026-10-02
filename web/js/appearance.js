import { app } from "/scripts/app.js";

const COLOR_THEMES = {
    primary: { nodeColor: "#222e40", nodeBgColor: "#364254", width: 340 },
    utility: { nodeColor: "#2e3e57", nodeBgColor: "#4b5b73", width: 300 },
};

const NODE_COLORS = {
    "DepthAnything3": "primary",
};

function setNodeColors(node, theme) {
    if (!theme) return;
    if (theme.nodeColor) node.color = theme.nodeColor;
    if (theme.nodeBgColor) node.bgcolor = theme.nodeBgColor;
    if (theme.width) {
        node.size = node.size || [140, 80];
        node.size[0] = theme.width;
    }
}

const ext = {
    name: "1038lab.DA3.appearance",
    nodeCreated(node) {
        const nclass = node.comfyClass;
        if (NODE_COLORS.hasOwnProperty(nclass)) {
            setNodeColors(node, COLOR_THEMES[NODE_COLORS[nclass]]);
        }
    }
};

app.registerExtension(ext);
