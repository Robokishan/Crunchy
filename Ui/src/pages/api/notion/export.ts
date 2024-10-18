import { NextApiRequest, NextApiResponse } from "next";
import { showError } from "~/utils/apis";
import { savePage } from "~/utils/apis/notion/database";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const { method } = req;
    if (method == "POST") {
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
      try {
        let _database_id = databaseId;
        if (!databaseId) {
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
        });
        res.status(200).json({
          message: _data,
        });
      } catch (error) {
        console.error({ message: "EXPORT_NOTION", error });
        res.status(400).json({
          message: "Something went wrong",
        });
      }
    } else {
      res.setHeader("Allow", ["POST"]);
      res.status(405).end(`Method ${method} Not Allowed`);
    }
  } catch (error) {
    console.error(error);
    showError(res);
  }
}
