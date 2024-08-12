;
var mod_reset_pwd_ops = {
    init:function(){
        this.eventBind();
    },
    eventBind:function(){
        //用id取#save
        $("#save").click(function(){
            var btn_target = $(this);
            if( btn_target.hasClass("disabled") ){
                common_ops.alert("正在处理!!请不要重复提交~~");
                return;
            }

            //old_password 原密码  new_password 新密码
            var old_password = $("#old_password").val();
            var new_password = $("#new_password").val();



            if( !old_password){
                common_ops.alert( "请输入原密码~~" );
                return false;
            };

            if( !new_password || new_password.length < 6 ){
                common_ops.alert( "请输入的新密码~~");
                return false;
            };

            btn_target.addClass("disabled");

            var data = {
                old_password : old_password,
                new_password : new_password
            }

            $.ajax({
                url:common_ops.buildUrl( "/user/reset_pwd" ),
                type:'POST',
                data:data,
                dataType:'json',
                success:function( res ){
                    btn_target.removeClass("disabled");
                    var callback = null;
                    if( res.code == 200 ){
                        callback = function(){
                            window.location.href = window.location.href;
                        }
                    }
                    common_ops.alert( res.msg,callback );
                }
            });

        });
    }
};

$(document).ready( function(){
    mod_reset_pwd_ops.init();
} );