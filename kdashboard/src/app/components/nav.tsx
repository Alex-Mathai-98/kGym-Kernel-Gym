"use client";

import React from "react";
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button } from "@nextui-org/react";

export function DashboardNav() {
  return (
    <Navbar className="backdrop-blur-lg" maxWidth="lg" isBordered>
      <NavbarBrand>
        <p className="font-bold text-inherit">KBDr</p>
      </NavbarBrand>
      <NavbarContent className="hidden sm:flex gap-4" justify="center">
        <NavbarItem>
          <Link color="foreground" href="/jobs">
            Jobs
          </Link>
        </NavbarItem>
        <NavbarItem>
        <Dropdown>
          <DropdownTrigger>
            <Link color="foreground">
              Displays
            </Link>
          </DropdownTrigger>
          <DropdownMenu className="text-foreground bg-background" aria-label="Static Actions">
            <DropdownItem key="job-log-display" href="/displays/jobs">
              Job Log Display
            </DropdownItem>
            <DropdownItem key="worker-log-display" href="/displays/workers">
              Worker Log Display
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
        </NavbarItem>
        <NavbarItem>
          <Link color="foreground" href="/analysis">
            Analysis
          </Link>
        </NavbarItem>
      </NavbarContent>
      <NavbarContent justify="end">
        <NavbarItem>
          <Button as={Link} color="primary" href="/compose" variant="flat">
            Compose
          </Button>
        </NavbarItem>
      </NavbarContent>
    </Navbar>
  );
}
