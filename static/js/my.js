/*!
  * 2021-01-18
  * Copyright 2011-2020 zhang xuzhou
  */
//<!--更新用户名-->
    function getuser(){
        $('#usernames').text("");
//<!--        $('#usernames').append('<option value=""></option>');-->
        var dept = $("#dept").val()
        $.ajax({
            url:"/getuser/" + dept,
            type:"post",
            success:function(data){
                for (var x in data) {
                    $('#usernames').append('<option value=' + x + '>' + data[x] +'</option>');
                    };
            },
        });
    }


$(document).ready(function(){
    $("#btn_add").click(function(event){
        event.preventDefault();
        var username=$('#username').val();
       if (username ==='' ) {
           alert('请输入信息');
           return false;
       }
        alert('pass');
        $.ajax({
            type: 'POST',
            url: '/addNewUser',
            data: $("#addNewUser").serialize(),
            datatype: 'json',
            success: function(data){
                $('input').val('');
                console.log(data.msg);
                location.reload();
            },
            error: function(data){
                console.log(data.msg);
            }
        });
    });

});