import DarkMode from "@mui/icons-material/DarkMode";
import LightMode from "@mui/icons-material/LightMode";
import MenuIcon from "@mui/icons-material/Menu";
import SettingsBrightness from "@mui/icons-material/SettingsBrightness";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Toolbar from "@mui/material/Toolbar";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useTheme } from "@mui/material/styles";
import { Link, useLocation } from "react-router-dom";
import * as React from "react";
import { useCallback } from "react";
import { useThemeMode } from "~/contexts/ThemeContext";
import { useHeaderScroll } from "~/contexts/HeaderScrollContext";

const pages = [
  {
    name: "Home",
    href: "/",
  },
  {
    name: "Connections",
    href: "/connections",
  },
  {
    name: "Settings",
    href: "/settings",
  },
];

function ResponsiveAppBar() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const { mode, setMode } = useThemeMode();
  const { headerHidden, scrollContainerRef } = useHeaderScroll();
  const location = useLocation();
  const isHome = location.pathname === "/";
  const hideHeader = isHome && headerHidden;

  const scrollChromeIntoView = useCallback(() => {
    if (!isHome || !isMobile) return;
    const el = scrollContainerRef.current;
    if (el) {
      el.scrollTop = 0;
      el.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [isHome, isMobile, scrollContainerRef]);

  const tryScrollChrome = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (!isHome || !isMobile) return;
      const target = e.target as HTMLElement;
      if (target.closest("button, a, [role='button'], input")) return;
      scrollChromeIntoView();
    },
    [isHome, isMobile, scrollChromeIntoView]
  );
  const handleAppBarClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => tryScrollChrome(e),
    [tryScrollChrome]
  );
  const handleAppBarTouchEnd = useCallback(
    (e: React.TouchEvent<HTMLDivElement>) => tryScrollChrome(e),
    [tryScrollChrome]
  );
  const [anchorElNav, setAnchorElNav] = React.useState<null | HTMLElement>(
    null
  );
  const [anchorElUser, setAnchorElUser] = React.useState<null | HTMLElement>(
    null
  );
  const isThemeActive = (m: "system" | "dark" | "light") => mode === m;
  const isNavActive = (href: string) =>
    href === "/" ? location.pathname === "/" : location.pathname.startsWith(href);

  const handleOpenNavMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNav(event.currentTarget);
  };
  const handleOpenUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  return (
    <AppBar
      position="sticky"
      elevation={0}
      onClick={handleAppBarClick}
      onTouchEnd={handleAppBarTouchEnd}
      sx={{
        top: 0,
        left: 0,
        right: 0,
        minWidth: 0,
        maxWidth: "100vw",
        width: "100%",
        zIndex: 9999,
        background: "linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
        transform: hideHeader ? "translateY(-100%)" : "none",
        transition: "transform 0.2s ease-out",
        pointerEvents: hideHeader ? "none" : "auto",
      }}
    >
      <Container maxWidth="xl" sx={{ minWidth: 0, maxWidth: "100%", width: "100%" }}>
        <Toolbar disableGutters sx={{ minHeight: { xs: 56, md: 64 }, px: { xs: 1, sm: 2 }, minWidth: 0 }}>
          {/* On mobile: no flexGrow so the tappable blank Box gets the middle; on desktop this is hidden */}
          <Box sx={{ flexGrow: { xs: 0, md: 0 }, display: { xs: "flex", md: "none" } }}>
            <IconButton
              size="large"
              aria-label="Open menu"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleOpenNavMenu}
              color="inherit"
              sx={{
                "&:hover": { backgroundColor: "rgba(255,255,255,0.12)" },
                "&:focus-visible": { boxShadow: "0 0 0 3px rgba(255,255,255,0.35)" },
              }}
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorElNav}
              anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
              keepMounted
              transformOrigin={{ vertical: "top", horizontal: "left" }}
              open={Boolean(anchorElNav)}
              onClose={handleCloseNavMenu}
              disableScrollLock
              sx={{
                display: { xs: "block", md: "none" },
                "& .MuiPaper-root": { borderRadius: 2, mt: 1.5, minWidth: 180 },
              }}
            >
              {pages.map(({ name, href }) => (
                <MenuItem key={name} onClick={handleCloseNavMenu} component={Link} to={href}>
                  <Typography sx={{ fontWeight: isNavActive(href) ? 600 : 400 }}>
                    {name}
                  </Typography>
                </MenuItem>
              ))}
              <MenuItem onClick={() => { setMode("system"); handleCloseNavMenu(); }}>
                <SettingsBrightness sx={{ mr: 1.5, fontSize: 20 }} /> System
              </MenuItem>
              <MenuItem onClick={() => { setMode("dark"); handleCloseNavMenu(); }}>
                <DarkMode sx={{ mr: 1.5, fontSize: 20 }} /> Dark
              </MenuItem>
              <MenuItem onClick={() => { setMode("light"); handleCloseNavMenu(); }}>
                <LightMode sx={{ mr: 1.5, fontSize: 20 }} /> Light
              </MenuItem>
            </Menu>
          </Box>

          {/* Spacer so theme icons stay right; tap handled by AppBar onClick */}
          {isMobile && (
            <Box
              sx={{
                flex: 1,
                minWidth: 0,
                minHeight: "100%",
                cursor: isHome ? "pointer" : "default",
                display: { xs: "block", md: "none" },
              }}
              aria-hidden
            />
          )}

          <Box sx={{ flexGrow: 1, display: { xs: "none", md: "flex" }, alignItems: "center", gap: 0.5 }}>
            {pages.map(({ name, href }) => (
              <Link key={name} to={href} style={{ textDecoration: "none" }}>
                <Button
                  sx={{
                    color: "white",
                    fontWeight: isNavActive(href) ? 600 : 500,
                    opacity: isNavActive(href) ? 1 : 0.9,
                    px: 2,
                    py: 1.5,
                    borderRadius: 2,
                    "&:hover": {
                      backgroundColor: "rgba(255,255,255,0.12)",
                      opacity: 1,
                    },
                    "&:focus-visible": {
                      boxShadow: "0 0 0 3px rgba(255,255,255,0.35)",
                    },
                  }}
                >
                  {name}
                </Button>
              </Link>
            ))}
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
            <Tooltip title="System theme">
              <IconButton
                color="inherit"
                onClick={() => setMode("system")}
                aria-label="Theme: System"
                size="medium"
                sx={{
                  backgroundColor: isThemeActive("system") ? "rgba(255,255,255,0.22)" : "transparent",
                  "&:hover": { backgroundColor: "rgba(255,255,255,0.12)" },
                  "&:focus-visible": { boxShadow: "0 0 0 3px rgba(255,255,255,0.35)" },
                }}
              >
                <SettingsBrightness sx={{ fontSize: 22 }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Dark mode">
              <IconButton
                color="inherit"
                onClick={() => setMode("dark")}
                aria-label="Theme: Dark"
                size="medium"
                sx={{
                  backgroundColor: isThemeActive("dark") ? "rgba(255,255,255,0.22)" : "transparent",
                  "&:hover": { backgroundColor: "rgba(255,255,255,0.12)" },
                  "&:focus-visible": { boxShadow: "0 0 0 3px rgba(255,255,255,0.35)" },
                }}
              >
                <DarkMode sx={{ fontSize: 22 }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Light mode">
              <IconButton
                color="inherit"
                onClick={() => setMode("light")}
                aria-label="Theme: Light"
                size="medium"
                sx={{
                  backgroundColor: isThemeActive("light") ? "rgba(255,255,255,0.22)" : "transparent",
                  "&:hover": { backgroundColor: "rgba(255,255,255,0.12)" },
                  "&:focus-visible": { boxShadow: "0 0 0 3px rgba(255,255,255,0.35)" },
                }}
              >
                <LightMode sx={{ fontSize: 22 }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
export default ResponsiveAppBar;
