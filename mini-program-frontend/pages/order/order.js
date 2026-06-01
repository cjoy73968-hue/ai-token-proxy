// AI Token 代理服务系统
// Copyright (C) 2026
// License: GNU General Public License v3.0
// https://www.gnu.org/licenses/

const app = getApp();

Page({
  data: {
    orders: []
  },

  onShow() {
    this.getOrders();
  },

  getOrders() {
    const openid = wx.getStorageSync('openid');
    if (!openid) return;
    wx.request({
      url: `${app.globalData.apiBase}/api/order-list`,
      data: { openid },
      success: res => {
        if (res.data.code === 200) {
          this.setData({ orders: res.data.data });
        }
      }
    });
  }
});