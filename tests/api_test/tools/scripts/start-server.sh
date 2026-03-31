#!/bin/bash
set -e

# 使用环境变量替换配置模板
envsubst < /etc/ctx/ctx.conf.template > /etc/ctx/ctx.conf

echo "Generated configuration:"
cat /etc/ctx/ctx.conf

# 启动AtomCtx服务
exec atom_ctx server start
