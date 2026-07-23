import { Command } from "commander";
import { getClient, emit, fail } from "../client.js";

export function sessionCommand(): Command {
  const session = new Command("session").description("Session commands");

  session
    .command("list")
    .description("List active sessions")
    .option("--pretty", "Indent JSON output", false)
    .action(async (opts: { pretty: boolean }) => {
      const client = getClient();
      try {
        const result = await client.sessions.list();
        emit(result, opts.pretty);
      } catch (e) {
        fail(e);
      }
    });

  return session;
}
