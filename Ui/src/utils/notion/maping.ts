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

  let properties: any = {
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
    Crunchbase: {
      type: "url",
      url: crunchbaseUrl,
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
  };

  if (founded) {
    properties = {
      ...properties,
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
    };
  }

  if (acquired) {
    properties = {
      ...properties,
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
    };
  }

  if (_funding) {
    properties = {
      ...properties,
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
    };
  }

  if (country) {
    properties = {
      ...properties,
      Country: {
        type: "select",
        select: {
          name: country,
        },
      },
    };
  }

  if (stocksymbol) {
    properties = {
      ...properties,
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

  if (lastfunding) {
    properties = {
      ...properties,
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
    };
  }

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
    properties: properties,
  };

  return payload;
};
