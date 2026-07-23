import { Command } from "commander";

export function authCommand(): Command {
  const auth = new Command("auth").description("Auth helper commands");

  auth
    .command("login")
    .description("Save an API key for future commands (run `ghostcrawl init`)")
    .action(() => {
      process.stderr.write(
        "Run `ghostcrawl init` to save an API key, or set GHOSTCRAWL_API_KEY.\n",
      );
      process.exit(0);
    });

  return auth;
}
