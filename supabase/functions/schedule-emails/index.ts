import { createHandler } from "./worker.ts";

Deno.serve(createHandler());
