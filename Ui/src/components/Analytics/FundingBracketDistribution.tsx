import {
  Box,
  ButtonBase,
  Chip,
  CircularProgress,
  Divider,
  LinearProgress,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import { useQuery } from "@tanstack/react-query";
import { memo, startTransition, useEffect, useState, useTransition } from "react";
import { Virtuoso } from "react-virtuoso";
import type {
  FundingBracketIndustryRow,
  FundingBracketDistributionBracket,
  FundingBracketDistributionResponse,
} from "~/utils/types";
import crunchyClient from "~/utils/crunchyClient";

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCompactCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatPercent(
  value: number,
  {
    minimumFractionDigits = 0,
    maximumFractionDigits = 0,
  }: {
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  } = {}
) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(value);
}

function formatRailPercent(value: number) {
  if (value < 0.01) {
    return formatPercent(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }
  if (value < 0.1) {
    return formatPercent(value, { maximumFractionDigits: 1 });
  }
  return formatPercent(value);
}

function formatCount(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatAxisMoneyLabel(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  })
    .format(value)
    .replace(".0", "");
}

function railRangeLabels(bracket: FundingBracketDistributionBracket) {
  if (bracket.max == null) {
    return {
      upper: `${formatAxisMoneyLabel(bracket.min)}+`,
      lower: formatAxisMoneyLabel(bracket.min),
    };
  }

  return {
    upper: formatAxisMoneyLabel(bracket.max),
    lower: formatAxisMoneyLabel(bracket.min),
  };
}

function RailShareLabel({ value }: { value: number }) {
  return (
    <Typography
      sx={{
        fontSize: { xs: 7.5, md: 8 },
        lineHeight: 1.1,
        fontWeight: 700,
        color: alpha("#f8fbff", 0.68),
        textAlign: "center",
        whiteSpace: "nowrap",
      }}
    >
      {formatRailPercent(value)}
    </Typography>
  );
}

const IndustryBreakdownRow = memo(function IndustryBreakdownRow({
  industry,
  index,
  maxIndustryCount,
}: {
  industry: FundingBracketIndustryRow;
  index: number;
  maxIndustryCount: number;
}) {
  const ratio = maxIndustryCount > 0 ? industry.company_count / maxIndustryCount : 0;
  const isTopTier = index < 3;

  return (
    <Box sx={{ pb: 1.25 }}>
      <Paper
        variant="outlined"
        sx={{
          borderRadius: "18px",
          borderColor: alpha(
            isTopTier ? "#4f8cff" : "#9fb2d0",
            isTopTier ? 0.2 : 0.12
          ),
          bgcolor: alpha("#0b1321", isTopTier ? 0.54 : 0.42),
          p: 1.75,
        }}
      >
        <Stack spacing={1.15}>
          <Stack
            direction="row"
            justifyContent="space-between"
            spacing={2}
            alignItems="center"
          >
            <Stack direction="row" spacing={1.25} alignItems="center" minWidth={0}>
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: "999px",
                  flexShrink: 0,
                  bgcolor: isTopTier ? "#63c8f7" : alpha("#cbd5e1", 0.6),
                  boxShadow: isTopTier
                    ? "0 0 0 4px rgba(99, 200, 247, 0.12)"
                    : "none",
                }}
              />
              <Typography
                sx={{
                  minWidth: 0,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  fontSize: 15,
                  fontWeight: 700,
                  color: "#f8fbff",
                }}
              >
                {industry.industry}
              </Typography>
            </Stack>

            <Stack direction="row" spacing={1.25} alignItems="center" flexShrink={0}>
              <Chip
                label={`${formatCount(industry.company_count)} companies`}
                size="small"
                sx={{
                  height: 28,
                  borderRadius: "999px",
                  bgcolor: alpha("#4f8cff", 0.12),
                  border: `1px solid ${alpha("#4f8cff", 0.18)}`,
                  color: "#dbeafe",
                  fontWeight: 700,
                }}
              />
              <Tooltip title={formatCurrency(industry.total_funding_usd)}>
                <Typography
                  sx={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: alpha("#f8fbff", 0.84),
                  }}
                >
                  {formatCompactCurrency(industry.total_funding_usd)}
                </Typography>
              </Tooltip>
            </Stack>
          </Stack>

          <LinearProgress
            variant="determinate"
            value={Math.max(ratio * 100, 4)}
            sx={{
              height: 8,
              borderRadius: "999px",
              bgcolor: alpha("#d7e2f1", 0.1),
              "& .MuiLinearProgress-bar": {
                borderRadius: "999px",
                background: isTopTier
                  ? "linear-gradient(90deg, #63c8f7 0%, #2f72e3 100%)"
                  : "linear-gradient(90deg, #9fb2d0 0%, #73829e 100%)",
              },
            }}
          />
        </Stack>
      </Paper>
    </Box>
  );
});

function barGradient(index: number, total: number, isSelected: boolean) {
  if (isSelected) {
    return "linear-gradient(180deg, #58d3f6 0%, #2f72e3 100%)";
  }

  const progress = total > 1 ? index / (total - 1) : 0;
  if (progress < 0.33) {
    return "linear-gradient(180deg, #c9d3e5 0%, #97a7c2 100%)";
  }
  if (progress < 0.66) {
    return "linear-gradient(180deg, #b9c7de 0%, #8198bb 100%)";
  }
  return "linear-gradient(180deg, #a9c8e0 0%, #6f91c9 100%)";
}

function chooseDefaultBracket(brackets: FundingBracketDistributionBracket[]) {
  if (brackets.length === 0) return null;

  const sorted = [...brackets].sort((left, right) => {
    if (right.company_count !== left.company_count) {
      return right.company_count - left.company_count;
    }
    return left.label.localeCompare(right.label);
  });
  return sorted[0]?.key ?? brackets[0].key;
}

export function FundingBracketDistribution() {
  const theme = useTheme();
  const [activeBracketKey, setActiveBracketKey] = useState<string | null>(null);
  const [detailBracketKey, setDetailBracketKey] = useState<string | null>(null);
  const [isPendingSelection, startSelectionTransition] = useTransition();

  const distributionQuery = useQuery({
    queryKey: ["funding-bracket-distribution"],
    queryFn: async () => {
      const { data } = await crunchyClient.get<FundingBracketDistributionResponse>(
        "/public/analytics/funding-bracket-distribution"
      );
      return data;
    },
    placeholderData: (previousData) => previousData,
  });

  const data = distributionQuery.data;
  const brackets = data?.brackets ?? [];
  const maxBracketCount = brackets.reduce(
    (currentMax, bracket) => Math.max(currentMax, bracket.company_count),
    0
  );

  useEffect(() => {
    if (brackets.length === 0) return;
    if (activeBracketKey && brackets.some((bracket) => bracket.key === activeBracketKey)) {
      return;
    }
    const defaultBracketKey = chooseDefaultBracket(brackets);
    setActiveBracketKey(defaultBracketKey);
    startTransition(() => {
      setDetailBracketKey(defaultBracketKey);
    });
  }, [activeBracketKey, brackets]);

  const selectedBracket =
    brackets.find((bracket) => bracket.key === detailBracketKey) ??
    brackets.find((bracket) => bracket.key === activeBracketKey) ??
    brackets[0] ??
    null;

  const maxIndustryCount = selectedBracket
    ? selectedBracket.industries.reduce(
        (currentMax, industry) => Math.max(currentMax, industry.company_count),
        0
      )
    : 0;

  const shellBorder = alpha("#9fb2d0", 0.14);
  const shellBackground =
    theme.palette.mode === "dark"
      ? "linear-gradient(180deg, #243146 0%, #1b2436 100%)"
      : "linear-gradient(180deg, #2a3951 0%, #1f2a3f 100%)";
  const mutedText = alpha("#edf3ff", 0.68);
  const softText = alpha("#edf3ff", 0.5);
  const selectedBorder = alpha("#4f8cff", 0.88);

  return (
    <section className="card-base !overflow-hidden !p-0">
      <Box
        sx={{
          borderRadius: "inherit",
          border: `1px solid ${shellBorder}`,
          background: shellBackground,
          px: { xs: 2, md: 3, xl: 4 },
          py: { xs: 2.5, md: 3, xl: 3.5 },
        }}
      >
        <Stack spacing={{ xs: 2.5, xl: 3 }}>
          <Stack
            direction={{ xs: "column", xl: "row" }}
            spacing={2}
            justifyContent="space-between"
            alignItems={{ xs: "flex-start", xl: "flex-start" }}
          >
            <Box sx={{ maxWidth: 760 }}>
              <Typography
                sx={{
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  color: alpha("#7dd3fc", 0.92),
                }}
              >
                Overview Extension
              </Typography>
              <Typography
                sx={{
                  mt: 1,
                  fontSize: { xs: 28, md: 34 },
                  lineHeight: 1.05,
                  fontWeight: 700,
                  letterSpacing: "-0.03em",
                  color: "#f8fbff",
                }}
              >
                Funding Bracket Distribution
              </Typography>
              <Typography
                sx={{
                  mt: 1.25,
                  maxWidth: 700,
                  fontSize: 15,
                  lineHeight: 1.65,
                  color: mutedText,
                }}
              >
                Full-database funding distribution across fixed brackets, with each bracket
                opening into the full industry mix behind it. No top-N cap, no truncation.
              </Typography>
            </Box>

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              flexWrap="wrap"
              justifyContent={{ xs: "flex-start", xl: "flex-end" }}
              alignItems="center"
            >
              {distributionQuery.isFetching ? (
                <CircularProgress
                  size={20}
                  sx={{ color: alpha("#93c5fd", 0.96), mr: 0.5 }}
                />
              ) : null}
              <Chip
                label={`${formatCount(data?.summary.bracketed_companies ?? 0)} bracketed`}
                size="small"
                sx={{
                  height: 32,
                  borderRadius: "999px",
                  bgcolor: alpha("#7dd3fc", 0.12),
                  border: `1px solid ${alpha("#7dd3fc", 0.24)}`,
                  color: "#d9f5ff",
                  fontWeight: 700,
                }}
              />
              <Chip
                label={`${formatPercent(data?.summary.coverage_ratio ?? 0)} coverage`}
                size="small"
                sx={{
                  height: 32,
                  borderRadius: "999px",
                  bgcolor: alpha("#4f8cff", 0.12),
                  border: `1px solid ${alpha("#4f8cff", 0.24)}`,
                  color: "#dbeafe",
                  fontWeight: 700,
                }}
              />
              <Chip
                label={`${formatCount(data?.summary.excluded_without_industries ?? 0)} funded missing industries`}
                size="small"
                sx={{
                  height: 32,
                  borderRadius: "999px",
                  bgcolor: alpha("#cbd5e1", 0.08),
                  border: `1px solid ${alpha("#cbd5e1", 0.14)}`,
                  color: alpha("#f8fbff", 0.82),
                  fontWeight: 700,
                }}
              />
            </Stack>
          </Stack>

          {brackets.length === 0 ? (
            <Paper
              variant="outlined"
              sx={{
                borderRadius: 4,
                borderColor: alpha("#cbd5e1", 0.12),
                bgcolor: alpha("#0a1220", 0.38),
                px: 3,
                py: 6,
              }}
            >
              <Typography sx={{ color: mutedText }}>
                No funded companies with industry tags are available yet.
              </Typography>
            </Paper>
          ) : (
            <>
              <Box
                sx={{
                  borderRadius: "28px",
                  border: `1px solid ${alpha("#9fb2d0", 0.12)}`,
                  bgcolor: alpha("#0a1220", 0.26),
                  px: { xs: 1.25, md: 1.75 },
                  py: { xs: 1.5, md: 1.75 },
                }}
              >
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${Math.max(brackets.length, 1)}, minmax(0, 1fr))`,
                    gap: { xs: "2px", md: "4px" },
                    alignItems: "end",
                  }}
                >
                  {brackets.map((bracket, index) => {
                    const ratio =
                      maxBracketCount > 0 ? bracket.company_count / maxBracketCount : 0;
                    const barHeight =
                      bracket.company_count > 0 ? Math.max(ratio * 100, 10) : 6;
                    const isSelected = bracket.key === activeBracketKey;
                    const rangeLabels = railRangeLabels(bracket);

                    return (
                      <ButtonBase
                        key={bracket.key}
                        focusRipple
                        aria-pressed={isSelected}
                        onClick={() => {
                          if (bracket.key === activeBracketKey) return;
                          setActiveBracketKey(bracket.key);
                          startSelectionTransition(() => {
                            setDetailBracketKey(bracket.key);
                          });
                        }}
                        sx={{
                          alignItems: "stretch",
                          justifyContent: "stretch",
                          borderRadius: "12px",
                          textAlign: "left",
                          p: { xs: 0.2, md: 0.3 },
                          backgroundColor: isSelected
                            ? alpha("#10233f", 0.42)
                            : "transparent",
                          outline: isSelected
                            ? `1px solid ${selectedBorder}`
                            : "1px solid transparent",
                          transition: "outline-color 180ms ease, background-color 180ms ease",
                          "&:hover": {
                            backgroundColor: isSelected
                              ? alpha("#10233f", 0.5)
                              : alpha("#10233f", 0.18),
                          },
                        }}
                      >
                        <Stack spacing={0.35} sx={{ width: "100%" }}>
                          <Tooltip
                            title={`${bracket.label}: ${formatCount(bracket.company_count)} companies, ${formatRailPercent(bracket.share_of_funded_companies)}`}
                          >
                            <Box
                              sx={{
                                minHeight: { xs: 138, md: 148 },
                                borderRadius: "10px",
                                px: { xs: 0.32, md: 0.38 },
                                py: 0.3,
                                display: "flex",
                                alignItems: "flex-end",
                                position: "relative",
                              }}
                            >
                              <Typography
                                sx={{
                                  position: "absolute",
                                  left: "50%",
                                  bottom: `calc(${barHeight}% + 6px)`,
                                  transform: "translateX(-50%)",
                                  px: 0.15,
                                  fontSize: { xs: 6.1, md: 6.5 },
                                  lineHeight: 1,
                                  fontWeight: 700,
                                  letterSpacing: "-0.015em",
                                  color: isSelected
                                    ? alpha("#e0f2fe", 0.92)
                                    : alpha("#f8fbff", 0.6),
                                  textAlign: "center",
                                  whiteSpace: "nowrap",
                                  pointerEvents: "none",
                                }}
                              >
                                {rangeLabels.upper}
                              </Typography>
                              <Box
                                sx={{
                                  width: "100%",
                                  minHeight: 14,
                                  height: `${barHeight}%`,
                                  borderRadius: "10px 10px 8px 8px",
                                  background: barGradient(index, brackets.length, isSelected),
                                  boxShadow: isSelected
                                    ? "0 12px 24px rgba(47, 114, 227, 0.28)"
                                    : "0 8px 14px rgba(7, 13, 24, 0.14)",
                                }}
                              />
                            </Box>
                          </Tooltip>

                          <Typography
                            sx={{
                              minHeight: 12,
                              px: 0.15,
                              fontSize: { xs: 6.1, md: 6.5 },
                              lineHeight: 1,
                              fontWeight: 700,
                              letterSpacing: "-0.015em",
                              color: isSelected
                                ? "#f8fbff"
                                : alpha("#f8fbff", 0.8),
                              textAlign: "center",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {rangeLabels.lower}
                          </Typography>
                          <RailShareLabel value={bracket.share_of_funded_companies} />
                        </Stack>
                      </ButtonBase>
                    );
                  })}
                </Box>
              </Box>

              {selectedBracket ? (
                <Box
                  sx={{
                    opacity: isPendingSelection ? 0.96 : 1,
                    display: "grid",
                    gap: 2,
                    gridTemplateColumns: {
                      xs: "1fr",
                      xl: "340px minmax(0, 1fr)",
                    },
                  }}
                >
                  <Paper
                    variant="outlined"
                    sx={{
                      borderRadius: "24px",
                      borderColor: alpha("#9fb2d0", 0.14),
                      bgcolor: alpha("#0a1220", 0.34),
                      p: 2.5,
                    }}
                  >
                    <Chip
                      label="Selected bracket"
                      size="small"
                      sx={{
                        height: 30,
                        borderRadius: "999px",
                        bgcolor: alpha("#4f8cff", 0.16),
                        border: `1px solid ${alpha("#4f8cff", 0.24)}`,
                        color: "#dbeafe",
                        fontWeight: 700,
                      }}
                    />
                    <Typography
                      sx={{
                        mt: 1.75,
                        fontSize: 30,
                        lineHeight: 1,
                        fontWeight: 700,
                        letterSpacing: "-0.03em",
                        color: "#f8fbff",
                      }}
                    >
                      {selectedBracket.label}
                    </Typography>
                    <Typography
                      sx={{
                        mt: 1.5,
                        fontSize: 14,
                        lineHeight: 1.6,
                        color: mutedText,
                      }}
                    >
                      Industry totals can overlap here because a single company may belong to
                      multiple industry tags.
                    </Typography>

                    <Stack spacing={2} sx={{ mt: 3 }}>
                      {[
                        {
                          label: "Companies",
                          value: formatCount(selectedBracket.company_count),
                        },
                        {
                          label: "Share of funded companies",
                          value: formatRailPercent(selectedBracket.share_of_funded_companies),
                        },
                        {
                          label: "Median funding",
                          value: formatCompactCurrency(selectedBracket.median_funding_usd),
                          title: formatCurrency(selectedBracket.median_funding_usd),
                        },
                        {
                          label: "Total funding",
                          value: formatCompactCurrency(selectedBracket.total_funding_usd),
                          title: formatCurrency(selectedBracket.total_funding_usd),
                        },
                        {
                          label: "Industries represented",
                          value: formatCount(selectedBracket.industry_count),
                        },
                      ].map((item) => (
                        <Box key={item.label}>
                          <Typography
                            sx={{
                              fontSize: 12,
                              fontWeight: 700,
                              letterSpacing: "0.12em",
                              textTransform: "uppercase",
                              color: softText,
                            }}
                          >
                            {item.label}
                          </Typography>
                          <Tooltip title={item.title ?? item.value}>
                            <Typography
                              sx={{
                                mt: 0.75,
                                fontSize: 26,
                                lineHeight: 1.05,
                                fontWeight: 700,
                                color: "#f8fbff",
                              }}
                            >
                              {item.value}
                            </Typography>
                          </Tooltip>
                        </Box>
                      ))}
                    </Stack>

                    <Divider sx={{ my: 2.5, borderColor: alpha("#9fb2d0", 0.12) }} />

                    <Stack spacing={1.25}>
                      <Typography
                        sx={{
                          fontSize: 12,
                          fontWeight: 700,
                          letterSpacing: "0.12em",
                          textTransform: "uppercase",
                          color: softText,
                        }}
                      >
                        Dataset health
                      </Typography>
                      <Stack direction="row" justifyContent="space-between" spacing={2}>
                        <Typography sx={{ fontSize: 14, color: mutedText }}>
                          Missing funding
                        </Typography>
                        <Typography sx={{ fontSize: 14, color: "#f8fbff", fontWeight: 700 }}>
                          {formatCount(data?.summary.excluded_without_funding ?? 0)}
                        </Typography>
                      </Stack>
                      <Stack direction="row" justifyContent="space-between" spacing={2}>
                        <Typography sx={{ fontSize: 14, color: mutedText }}>
                          Funded missing industries
                        </Typography>
                        <Typography sx={{ fontSize: 14, color: "#f8fbff", fontWeight: 700 }}>
                          {formatCount(data?.summary.excluded_without_industries ?? 0)}
                        </Typography>
                      </Stack>
                    </Stack>
                  </Paper>

                  <Paper
                    variant="outlined"
                    sx={{
                      borderRadius: "24px",
                      borderColor: alpha("#9fb2d0", 0.14),
                      bgcolor: alpha("#0a1220", 0.34),
                      p: 2.5,
                    }}
                  >
                    <Stack
                      direction={{ xs: "column", sm: "row" }}
                      spacing={1.5}
                      justifyContent="space-between"
                      alignItems={{ xs: "flex-start", sm: "center" }}
                    >
                      <Box>
                        <Typography
                          sx={{
                            fontSize: 22,
                            lineHeight: 1.1,
                            fontWeight: 700,
                            letterSpacing: "-0.02em",
                            color: "#f8fbff",
                          }}
                        >
                          Full industry breakdown
                        </Typography>
                        <Typography
                          sx={{
                            mt: 1,
                            fontSize: 14,
                            lineHeight: 1.6,
                            color: mutedText,
                          }}
                        >
                          Every industry attached to companies inside {selectedBracket.label}.
                        </Typography>
                      </Box>
                      <Chip
                        label={`${formatCount(selectedBracket.industry_count)} industries`}
                        size="small"
                        sx={{
                          height: 32,
                          borderRadius: "999px",
                          bgcolor: alpha("#cbd5e1", 0.08),
                          border: `1px solid ${alpha("#cbd5e1", 0.14)}`,
                          color: alpha("#f8fbff", 0.82),
                          fontWeight: 700,
                        }}
                      />
                    </Stack>

                    <Box sx={{ mt: 2.5 }}>
                      {selectedBracket.industries.length === 0 ? (
                        <Paper
                          variant="outlined"
                          sx={{
                            borderRadius: "18px",
                            borderColor: alpha("#cbd5e1", 0.12),
                            bgcolor: alpha("#0a1220", 0.38),
                            p: 3,
                          }}
                        >
                          <Typography sx={{ color: mutedText }}>
                            No industries found in this bracket.
                          </Typography>
                        </Paper>
                      ) : (
                        <Virtuoso
                          style={{ height: 500 }}
                          totalCount={selectedBracket.industries.length}
                          computeItemKey={(index) =>
                            `${selectedBracket.key}:${selectedBracket.industries[index].industry}`
                          }
                          defaultItemHeight={98}
                          fixedItemHeight={98}
                          increaseViewportBy={320}
                          itemContent={(index) => (
                            <IndustryBreakdownRow
                              index={index}
                              industry={selectedBracket.industries[index]}
                              maxIndustryCount={maxIndustryCount}
                            />
                          )}
                        />
                      )}
                    </Box>
                  </Paper>
                </Box>
              ) : null}
            </>
          )}
        </Stack>
      </Box>
    </section>
  );
}
