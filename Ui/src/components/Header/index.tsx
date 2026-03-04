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
import { Link } from "react-router-dom";
import * as React from "react";
import { useThemeMode } from "~/contexts/ThemeContext";

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
  const { mode, setMode } = useThemeMode();
  const [anchorElNav, setAnchorElNav] = React.useState<null | HTMLElement>(
    null
  );
  const [anchorElUser, setAnchorElUser] = React.useState<null | HTMLElement>(
    null
  );
  const isActive = (m: "system" | "dark" | "light") => mode === m;

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
    <AppBar position="static">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Box sx={{ flexGrow: 1, display: { xs: "flex", md: "none" } }}>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleOpenNavMenu}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorElNav}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "left",
              }}
              keepMounted
              transformOrigin={{
                vertical: "top",
                horizontal: "left",
              }}
              open={Boolean(anchorElNav)}
              onClose={handleCloseNavMenu}
              sx={{ display: { xs: "block", md: "none" } }}
            >
              {pages.map(({ name, href }) => (
                <MenuItem key={name} onClick={handleCloseNavMenu}>
                  <Link to={href}>
                    <Typography sx={{ textAlign: "center" }}>{name}</Typography>
                  </Link>
                </MenuItem>
              ))}
              <MenuItem onClick={() => { setMode("system"); handleCloseNavMenu(); }}>
                <SettingsBrightness sx={{ mr: 1 }} /> System
              </MenuItem>
              <MenuItem onClick={() => { setMode("dark"); handleCloseNavMenu(); }}>
                <DarkMode sx={{ mr: 1 }} /> Dark
              </MenuItem>
              <MenuItem onClick={() => { setMode("light"); handleCloseNavMenu(); }}>
                <LightMode sx={{ mr: 1 }} /> Light
              </MenuItem>
            </Menu>
          </Box>

          <Box sx={{ flexGrow: 1, display: { xs: "none", md: "flex" } }}>
            {pages.map(({ name, href }) => (
              <Link key={name} to={href}>
                <Button
                  sx={{
                    my: 2,
                    color: "white",
                    display: "block",
                  }}
                >
                  {name}
                </Button>
              </Link>
            ))}
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0 }}>
            <Tooltip title="System theme">
              <IconButton
                color="inherit"
                onClick={() => setMode("system")}
                aria-label="Theme: System"
                sx={{
                  backgroundColor: isActive("system") ? "rgba(255,255,255,0.2)" : undefined,
                  "&:hover": { backgroundColor: "rgba(255,255,255,0.1)" },
                }}
              >
                <SettingsBrightness />
              </IconButton>
            </Tooltip>
            <Tooltip title="Dark mode">
              <IconButton
                color="inherit"
                onClick={() => setMode("dark")}
                aria-label="Theme: Dark"
                sx={{
                  backgroundColor: isActive("dark") ? "rgba(255,255,255,0.2)" : undefined,
                  "&:hover": { backgroundColor: "rgba(255,255,255,0.1)" },
                }}
              >
                <DarkMode />
              </IconButton>
            </Tooltip>
            <Tooltip title="Light mode">
              <IconButton
                color="inherit"
                onClick={() => setMode("light")}
                aria-label="Theme: Light"
                sx={{
                  backgroundColor: isActive("light") ? "rgba(255,255,255,0.2)" : undefined,
                  "&:hover": { backgroundColor: "rgba(255,255,255,0.1)" },
                }}
              >
                <LightMode />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
export default ResponsiveAppBar;
