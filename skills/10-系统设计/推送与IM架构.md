---
title: 推送与 IM 架构
domain: 10-系统设计
level: 了解
target: 掌握
importance: 中
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-08-23
tags: [推送, IM, 长连接]
related: []
---

# 推送与 IM 架构

## 概述
长连接方案选型:厂商推送(FCM / 华米 OV)、自建 TCP / WebSocket、MQTT。设计点:**连接保活与心跳**、消息可靠送达(ACK / 重传 / 去重)、离线消息补偿、电量与后台限制(Android 后台策略)、多端消息同步。IM 还要考虑消息序号、已读、存储分库。

## 考核记录
（尚未考核）
