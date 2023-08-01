export interface MappingArg {
  iconUrl: string;
  website: string;
  crunchbaseUrl: string;
  founders: string[];
  funding: string;
  name: string;
  country: string;
  tags: string[];
  description: string;

  founded: string;
  lastfunding: string;
  stocksymbol: string;
  acquired: string;
}

export const mapToNotion = (databaseId: string, mapingData: MappingArg) => {
  console.log("Mapping data", mapingData);
  const {
    iconUrl,
    website,
    country,
    crunchbaseUrl,
    founders,
    funding,
    name,
    tags,
    description,
    acquired,
    founded,
    lastfunding,
    stocksymbol,
  } = mapingData;
  const _founders = founders.join(", ");
  const _funding = funding;

  const _tags = tags.map((tag) => ({
    name: tag,
  }));

  let payload: any = {
    icon: {
      type: "external",
      external: {
        url: iconUrl,
      },
    },
    parent: {
      database_id: databaseId,
    },
    properties: {
      Research: {
        type: "select",
        select: {
          name: "Not started",
          color: "orange",
        },
      },
      Domain: {
        type: "multi_select",
        multi_select: _tags,
      },

      Website: {
        type: "url",
        url: website,
      },
      Description: {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: description,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: description,
            href: null,
          },
        ],
      },
      Founders: {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: _founders,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: _founders,
            href: null,
          },
        ],
      },
      Funding: {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: _funding,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: _funding,
            href: null,
          },
        ],
      },
      Crunchbase: {
        type: "url",
        url: crunchbaseUrl,
      },
    
      Founded: {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: founded,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: founded,
            href: null,
          },
        ],
      },

      Name: {
        type: "title",
        title: [
          {
            type: "text",
            text: {
              content: name,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: name,
            href: null,
          },
        ],
      },
    },
  };

  if (country) {
    payload = {
      ...payload,
      Country: {
        type: "select",
        select: {
          name: country,
        },
      },
    };
  }

  if (stocksymbol) {
    payload = {
      ...payload,
      "Stock Symbol": {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: stocksymbol,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: stocksymbol,
            href: null,
          },
        ],
      },
    };
  }

  if(acquired) {
    payload = {
      ...payload,
      Acquired: {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: acquired,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: acquired,
            href: null,
          },
        ],
      },
    }
  }

  if(lastfunding) {
    payload = {
      ...payload,
      LastFunding: {
        type: "rich_text",
        rich_text: [
          {
            type: "text",
            text: {
              content: lastfunding,
              link: null,
            },
            annotations: {
              bold: false,
              italic: false,
              strikethrough: false,
              underline: false,
              code: false,
              color: "default",
            },
            plain_text: lastfunding,
            href: null,
          },
        ],
      },
    }
  }

  return payload;
};
