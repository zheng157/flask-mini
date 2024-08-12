//获取应用实例
var app = getApp();
Page({
    data: {},
    onShow: function () {
        var that = this;
        this.getList();
    },
    selectTap: function (e) {
        //从商品详情下单选择地址之后返回
        var that = this;
        var data = {
            id:e.currentTarget.dataset.id,
            act:'default'
        }
        wx.request({
            url: app.buildUrl("/my/address/ops"),
            header: app.getRequestHeader(),
            method:'POST',
            data:data,
            success: function (res) {
                var resp = res.data;
                if (resp.code != 200) {
                    app.alert({"content": resp.msg});
                    return;
                }
            },
        })
        wx.navigateBack({});
    },
    addressSet: function (e) {
        wx.navigateTo({
            url: "/pages/my/addressSet?id="+ e.currentTarget.dataset.id
        })
    },

    getList:function (){
        var that = this;
        wx.request({
            url: app.buildUrl("/my/address/index"),
            header: app.getRequestHeader(),
            success: function (res) {
                var resp = res.data;
                if (resp.code != 200) {
                    app.alert({"content": resp.msg});
                    return;
                }
                that.setData({
                   list:resp.data.list
                });

            }
        });

    }
});
