#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { UnityConnection } from "./unity-connection.js";
import { registerScriptTools } from "./tools/script-tools.js";
import { registerEditorTools } from "./tools/editor-tools.js";
import { registerTestingTools } from "./tools/testing-tools.js";
import { registerSceneTools } from "./tools/scene-tools.js";
import { registerGameObjectTools } from "./tools/gameobject-tools.js";
import { registerScreenshotTools } from "./tools/screenshot-tools.js";
import { registerDebugTools } from "./tools/debug-tools.js";

// Whitelist of minimal coding loop tools for Muse Code
const ALLOWED_TOOLS = new Set([
    // 1. Compile & Rebuild Loop
    "refresh_asset_db",
    "get_compilation_errors",
    // 2. Console logs & diagnostics
    "get_console_logs",
    "clear_console",
    // 3. Unit & Integration Testing
    "run_tests",
    // 4. Play mode verification
    "play_scene",
    "stop_scene",
    "get_play_state",
    // 5. Scene structure & GameObject inspection
    "get_hierarchy",
    "get_components",
    "find_gameobjects",
    // 6. Visual feedback
    "get_game_screenshot",
    "get_editor_screenshot",
]);

const unity = new UnityConnection(parseInt(process.env.UNITY_MCP_PORT || "6605"));
const baseServer = new McpServer({
    name: "unity-mcp-mini",
    version: "1.0.0",
});

let registeredCount = 0;
// Proxy to intercept and whitelist only tools in ALLOWED_TOOLS
const filteredServer = new Proxy(baseServer, {
    get(target, prop) {
        if (prop === "tool") {
            return (name, ...rest) => {
                if (ALLOWED_TOOLS.has(name)) {
                    registeredCount++;
                    return target.tool(name, ...rest);
                }
                // Silently skip non-essential tools
                return target;
            };
        }
        return Reflect.get(target, prop);
    },
});

// Register candidate tool modules through the filtered proxy
registerScriptTools(filteredServer, unity);
registerEditorTools(filteredServer, unity);
registerTestingTools(filteredServer, unity);
registerSceneTools(filteredServer, unity);
registerGameObjectTools(filteredServer, unity);
registerScreenshotTools(filteredServer, unity);
registerDebugTools(filteredServer, unity);

// Prevent unhandled errors from terminating the process
process.on("uncaughtException", (err) => {
    console.error("[MCP-Mini] Uncaught exception:", err.message);
});
process.on("unhandledRejection", (err) => {
    console.error("[MCP-Mini] Unhandled rejection:", err);
});

async function main() {
    await unity.connect().catch((err) => {
        console.error(`[MCP-Mini] Unity connection status: ${err.message}. Will retry on demand.`);
    });

    const transport = new StdioServerTransport();
    await baseServer.connect(transport);
    console.error(`[MCP-Mini] Unity MCP Mini started (${registeredCount} core tools registered, stdio transport)`);
}

main().catch((err) => {
    console.error("[MCP-Mini] Fatal error:", err);
    process.exit(1);
});
