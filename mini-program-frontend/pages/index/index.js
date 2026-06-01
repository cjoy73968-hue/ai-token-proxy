// AI Token 代理服务系统
// Copyright (C) 2026
// License: GNU General Public License v3.0
// https://www.gnu.org/licenses/

const app = getApp();

Page({
  data: {
    goodsList: []
  },

  onLoad() {
    this.loadPackages();
  },

  loadPackages() {
    wx.request({
      url: `${app.globalData.apiBase}/api/packages`,
      success: res => {
        if (res.data.code === 200 && res.data.packages) {
          const goodsList = res.data.packages.map(pkg => ({
            id: pkg.price,
            name: pkg.name,
            tag: `${pkg.models.length}个模型`,
            desc: pkg.description || `${pkg.service_quota}次服务配额`,
            price: pkg.price,
            original: pkg.price * 1.5,
            models: pkg.models,
            service_quota: pkg.service_quota
          }));
          this.setData({ goodsList });
        }
      }
    });
  },

  goPay(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/pay/pay?id=${id}`
    });
  }
});