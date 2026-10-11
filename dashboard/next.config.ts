import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // don't write AGENTS.md / CLAUDE.md into the project when `next dev` detects an AI coding agent
  agentRules: false,
};

export default nextConfig;
