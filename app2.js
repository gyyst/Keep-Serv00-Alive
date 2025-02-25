const express = require("express");
const path = require("path");
const exec = require("child_process").exec;
const execSync = require("child_process").execSync; // 新增同步执行模块
const app = express();
const port = 3000;

// 自动获取用户名
const user = execSync("whoami").toString().trim(); // 同步执行并去除换行符
const pName = "s5";

// 自定义命令数组（修改为函数形式动态生成）
const getProcesses = () => [
  `/home/${user}/.npm-global/bin/pm2 resurrect`,
  `/home/${user}/.npm-global/bin/pm2 save`,
  // 可以添加其他需要监控的命令
];

app.use(express.static(path.join(__dirname, 'static')));

// 增加启动时验证
console.log(`[系统启动] 当前用户：${user}`);
if (!user || user.length === 0) {
  console.error("无法获取用户名，请检查系统权限！");
  process.exit(1);
}

function keepWebAlive() {
  const now = new Date(); 
  getProcesses().forEach((command) => {
    exec(`${command}`, (err) => {
      const status = err ? `失败: ${err}` : "成功";
      console.log(`[${now.toLocaleString()}] 启动 ${status}: ${command}`);
    });
  });
}

setInterval(keepWebAlive, 5 * 60 * 1000);

app.listen(port, () => {
  console.log(`服务已启动 | 端口: ${port} | 用户: ${user}`);
});
