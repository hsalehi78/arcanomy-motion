import { Config } from "@remotion/cli/config";

Config.setEntryPoint("./src/index.ts");
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// Allow loading local file:// URLs during rendering
Config.setChromiumDisableWebSecurity(true);

