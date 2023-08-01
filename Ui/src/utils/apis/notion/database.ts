import { MappingArg, mapToNotion } from "~/utils/notion/maping";
import notionClient from "~/utils/notionServerClient";

const BASE_DATABASE = "/v1/databases";
const BASE_PAGE = "/v1/pages";

export const queryDatabase = async (id: string): Promise<any> => {
  const { data } = await notionClient.post(
    BASE_DATABASE + "/" + id + "/query",
    {}
  );
  return data;
};

export const retrieveDatabase = async (id: string): Promise<any> => {
  const { data } = await notionClient.get(BASE_DATABASE + "/" + id);
  return data;
};

export const retrievePage = async (id: string): Promise<any> => {
  const { data } = await notionClient.get(BASE_PAGE + "/" + id);
  return data;
};

export const listDatabases = async (): Promise<any> => {
  const { data } = await notionClient.get(BASE_DATABASE);
  return data;
};

export const savePage = async (
  databaseId: string,
  pageDetails: MappingArg
): Promise<any> => {
  const args = mapToNotion(databaseId, pageDetails);
  const { data } = await notionClient.post(BASE_PAGE, args);
  return data;
};
