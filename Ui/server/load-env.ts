import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..", "..");
const envFile =
  process.env.NODE_ENV === "production"
    ? path.join(rootDir, ".env.prod")
    : path.join(rootDir, ".env.dev");
dotenv.config({ path: envFile });
