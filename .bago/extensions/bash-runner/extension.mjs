// bash-runner — extensión BAGO-nativa para Copilot CLI
// Fuente de verdad: .bago/extensions/bash-runner/extension.mjs
// Instalada por `bago setup` en .github/extensions/bash-runner/
//
// Herramientas:
//   bash-runner_exec       — ejecuta cualquier comando shell
//   bash-runner_run_script — ejecuta un .sh por ruta
//   bash-runner_bago_run   — ejecuta comandos BAGO (auto-detecta BAGO_ROOT)

import { joinSession } from "@github/copilot-sdk/extension";
import { spawnSync } from "child_process";
import { existsSync } from "fs";
import { join, resolve } from "path";

function findBAGORoot(startDir) {
    let dir = resolve(startDir || process.cwd());
    for (let i = 0; i < 10; i++) {
        if (existsSync(join(dir, ".bago")) && existsSync(join(dir, "bago"))) return dir;
        const parent = resolve(dir, "..");
        if (parent === dir) break;
        dir = parent;
    }
    return null;
}

function runCmd(args, cwd, timeout = 30000) {
    const result = spawnSync(args[0], args.slice(1), {
        cwd: cwd || process.cwd(),
        timeout,
        encoding: "utf8",
        maxBuffer: 1024 * 1024 * 10,
        shell: false
    });
    return {
        stdout: result.stdout || "",
        stderr: result.stderr || "",
        exit_code: result.status ?? -1,
        error: result.error?.message || null
    };
}

const session = await joinSession({
    tools: [
        {
            name: "bash-runner_exec",
            description: "Ejecuta un comando shell en el sistema local. Usa esto cuando el bash tool del agente esté caído. Devuelve stdout, stderr y exit code.",
            parameters: {
                type: "object",
                properties: {
                    command: {
                        type: "string",
                        description: "El comando shell a ejecutar"
                    },
                    cwd: {
                        type: "string",
                        description: "Directorio de trabajo (opcional). Por defecto usa el directorio actual."
                    },
                    timeout: {
                        type: "number",
                        description: "Timeout en milisegundos (opcional, por defecto 30000)"
                    }
                },
                required: ["command"]
            },
            handler: async ({ command, cwd, timeout = 30000 }) => {
                try {
                    const result = spawnSync("bash", ["-c", command], {
                        cwd: cwd || process.cwd(),
                        timeout,
                        encoding: "utf8",
                        maxBuffer: 1024 * 1024 * 10
                    });
                    return JSON.stringify({
                        stdout: result.stdout || "",
                        stderr: result.stderr || "",
                        exit_code: result.status ?? -1,
                        error: result.error?.message || null
                    }, null, 2);
                } catch (err) {
                    return JSON.stringify({ error: err.message, exit_code: -1 });
                }
            }
        },

        {
            name: "bash-runner_run_script",
            description: "Ejecuta un archivo de script bash (.sh) existente en el sistema local.",
            parameters: {
                type: "object",
                properties: {
                    script_path: {
                        type: "string",
                        description: "Ruta absoluta al archivo .sh a ejecutar"
                    },
                    cwd: {
                        type: "string",
                        description: "Directorio de trabajo (opcional)"
                    }
                },
                required: ["script_path"]
            },
            handler: async ({ script_path, cwd }) => {
                try {
                    const result = spawnSync("bash", [script_path], {
                        cwd: cwd || process.cwd(),
                        timeout: 60000,
                        encoding: "utf8",
                        maxBuffer: 1024 * 1024 * 10
                    });
                    return JSON.stringify({
                        stdout: result.stdout || "",
                        stderr: result.stderr || "",
                        exit_code: result.status ?? -1,
                        error: result.error?.message || null
                    }, null, 2);
                } catch (err) {
                    return JSON.stringify({ error: err.message, exit_code: -1 });
                }
            }
        },

        {
            name: "bash-runner_bago_run",
            description: "Ejecuta un comando BAGO (setup, health, dashboard, validate, audit, stale, workflow, versions, cosecha...). Auto-detecta BAGO_ROOT desde el directorio de trabajo.",
            parameters: {
                type: "object",
                properties: {
                    bago_cmd: {
                        type: "string",
                        description: "Comando BAGO a ejecutar (ej: 'health', 'setup', 'validate', 'versions')"
                    },
                    bago_root: {
                        type: "string",
                        description: "Ruta al directorio raíz que contiene el script 'bago' y '.bago/'. Opcional — se auto-detecta desde cwd."
                    },
                    cwd: {
                        type: "string",
                        description: "Directorio de trabajo para la detección y ejecución (opcional)"
                    }
                },
                required: ["bago_cmd"]
            },
            handler: async ({ bago_cmd, bago_root, cwd }) => {
                try {
                    const workDir = cwd ? resolve(cwd) : process.cwd();
                    const root = bago_root ? resolve(bago_root) : findBAGORoot(workDir);

                    if (!root) {
                        return JSON.stringify({
                            error: "No se encontró .bago/ + script 'bago' en el directorio actual o sus padres.",
                            searched_from: workDir,
                            exit_code: -1
                        });
                    }

                    const bagoScript = join(root, "bago");
                    if (!existsSync(bagoScript)) {
                        return JSON.stringify({
                            error: `Script 'bago' no encontrado en: ${root}`,
                            exit_code: -1
                        });
                    }

                    // Separa el comando en tokens para pasar como args
                    const cmdArgs = bago_cmd.trim().split(/\s+/);
                    const result = runCmd(
                        ["python3", bagoScript, ...cmdArgs],
                        root,
                        30000
                    );
                    return JSON.stringify({ bago_root: root, ...result }, null, 2);
                } catch (err) {
                    return JSON.stringify({ error: err.message, exit_code: -1 });
                }
            }
        }
    ]
});
