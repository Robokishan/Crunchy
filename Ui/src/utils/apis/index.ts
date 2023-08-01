import { NextApiResponse } from "next";

export const showError = (
  res: NextApiResponse,
  message = "Something went wrong",
  statusCode = 400
) => {
  res.status(statusCode).json({
    error: message,
  });
};
