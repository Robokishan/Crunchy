import { NextApiRequest, NextApiResponse } from "next";
import { showError } from "~/utils/apis";
import {
  listDatabases,
  retrieveDatabase,
  retrievePage,
} from "~/utils/apis/notion/database";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const { method } = req;
    if (method == "GET") {
      const { database_id: databaseId, page_id: pageId } = req.query;
      if (databaseId) {
        const pages = await retrieveDatabase(databaseId as string);
        res.status(200).json(pages);
      } else if (pageId) {
        const page = await retrievePage(pageId as string);
        res.status(200).json(page);
      } else {
        const databases = await listDatabases();
        res.status(200).json(databases);
      }
    } else {
      res.setHeader("Allow", ["POST"]);
      res.status(405).end(`Method ${method} Not Allowed`);
    }
  } catch (error) {
    console.log(error);
    showError(res);
  }
}
