import "./load-env.js";
import express, { type Request, type Response, type NextFunction } from "express";
import path from "path";
import { fileURLToPath } from "url";
import {
  listDatabases,
  retrieveDatabase,
  retrievePage,
  savePage,
} from "../src/utils/apis/notion/database.js";
import type { MappingArg } from "../src/utils/notion/maping.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT ?? process.env.NOTION_API_PORT ?? 3001;

app.use(express.json());

// Serve Vite build in production
const distPath = path.join(__dirname, "..", "dist");
app.use(express.static(distPath));

app.get("/api/notion/retrieve", async (req: Request, res: Response) => {
  try {
    const { database_id: databaseId, page_id: pageId } = req.query;
    if (databaseId) {
      const pages = await retrieveDatabase(databaseId as string);
      return res.status(200).json(pages);
    }
    if (pageId) {
      const page = await retrievePage(pageId as string);
      return res.status(200).json(page);
    }
    const databases = await listDatabases();
    return res.status(200).json(databases);
  } catch (error) {
    console.error(error);
    return res.status(400).json({ error: "Something went wrong" });
  }
});

app.post("/api/notion/export", async (req: Request, res: Response) => {
  try {
    const {
      crunchbaseUrl,
      founders,
      funding,
      iconUrl,
      name,
      website,
      country,
      description,
      tags,
      database_id: databaseId,
      founded,
      lastfunding,
      stocksymbol,
      acquired,
    } = req.body;

    let _database_id = databaseId;
    if (!_database_id) {
      _database_id = process.env.NOTION_DATABASE_ID;
    }
    const _data = await savePage(_database_id, {
      country,
      description,
      tags,
      crunchbaseUrl,
      founders,
      funding,
      iconUrl,
      name,
      website,
      founded,
      lastfunding,
      stocksymbol,
      acquired,
    } as MappingArg);
    return res.status(200).json({ message: _data });
  } catch (error) {
    console.error({ message: "EXPORT_NOTION", error });
    return res.status(400).json({ message: "Something went wrong" });
  }
});

// SPA fallback: serve index.html for non-API routes
app.get("*", (req: Request, res: Response, next: NextFunction) => {
  if (req.path.startsWith("/api")) return next();
  res.sendFile(path.join(distPath, "index.html"), (err: Error | null) => {
    if (err) next(err);
  });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
