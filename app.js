const express = require("express");
const path = require("path");
const exec = require("child_process").exec;
const execSync = require("child_process").execSync; // 新增同步执行模块
const app = express();
const port = 3000;

// 引入 getProcesses 函数
const getProcesses = require("./processes");

// 自动获取用户名
const user = execSync("whoami").toString().trim(); // 同步执行并去除换行符

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

setInterval(keepWebAlive, 2 * 60 * 1000);

app.listen(port, () => {
  console.log(`服务已启动 | 端口: ${port} | 用户: ${user}`);
});
