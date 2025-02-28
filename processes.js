// processes.js

// 自动获取用户名
const user = require("child_process").execSync("whoami").toString().trim(); // 同步执行并去除换行符

// 自定义命令数组（修改为函数形式动态生成）
const getProcesses = () => [
  `/home/${user}/.npm-global/bin/pm2 resurrect`,
  `/home/${user}/.npm-global/bin/pm2 save`,
  // 可以添加其他需要监控的命令
];

module.exports = getProcesses;
