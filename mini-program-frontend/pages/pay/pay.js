// AI Token 代理服务系统
// Copyright (C) 2026
// License: GNU General Public License v3.0
// https://www.gnu.org/licenses/

const app = getApp();

Page({
  data: {
    goodsInfo: {},
    openid: "",
    loading: false,
    packages: []
  },

  onLoad(options) {
    const id = parseFloat(options.id);
    this.setData({ goodsInfo: { price: id } });
    this.loadPackages(id);
    this.getOpenid();
  },

  loadPackages(selectedPrice) {
    wx.request({
      url: `${app.globalData.apiBase}/api/packages`,
      success: res => {
        if (res.data.code === 200 && res.data.packages) {
          this.setData({ packages: res.data.packages });
          const pkg = res.data.packages.find(p => p.price === selectedPrice);
          if (pkg) {
            this.setData({
              goodsInfo: {
                id: pkg.price,
                name: pkg.name,
                desc: `${pkg.service_quota}万Token`,
                price: pkg.price,
                priceYuan: Math.round(pkg.price * 100),
                service_quota: pkg.service_quota
              }
            });
          }
        }
      }
    });
  },

  getOpenid() {
    let openid = wx.getStorageSync('openid');
    if (!openid) {
      wx.login({
        success: res => {
          if (res.code) {
            wx.request({
              url: `${app.globalData.apiBase}/api/get-openid`,
              data: { code: res.code },
              success: r => {
                openid = r.data.openid;
                wx.setStorageSync('openid', openid);
                this.setData({ openid });
              }
            });
          }
        }
      });
    } else {
      this.setData({ openid });
    }
  },

  submitPay() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    const templateId = app.globalData.templateId;
    wx.requestSubscribeMessage({
      tmplIds: [templateId],
      success: res => {
        if (res[templateId] === 'accept') {
          this.createOrder();
        } else {
          wx.showToast({ title: '需允许接收通知', icon: 'none' });
          this.setData({ loading: false });
        }
      },
      fail: () => {
        wx.showToast({ title: '授权失败', icon: 'none' });
        this.setData({ loading: false });
      }
    });
  },

  createOrder() {
    const { goodsInfo, openid } = this.data;
    wx.request({
      url: `${app.globalData.apiBase}/api/create-pay-order`,
      method: "POST",
      data: {
        openid: openid,
        goodsId: goodsInfo.id,
        totalFee: goodsInfo.priceYuan,
        body: goodsInfo.name
      },
      success: res => {
        if (res.data.code === 200) {
          const pay = res.data.data;
          wx.requestPayment({
            timeStamp: pay.timeStamp,
            nonceStr: pay.nonceStr,
            package: pay.package,
            signType: pay.signType,
            paySign: pay.paySign,
            success: () => {
              wx.showToast({ title: '支付成功' });
              setTimeout(() => wx.navigateBack(), 1500);
            },
            fail: () => {
              wx.showToast({ title: '支付取消', icon: 'none' });
            }
          });
        }
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  }
});