package com.example.faceattend;


import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.GET;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.Part;

public interface UploadApis {
    //@Multipart
    //@GET("hello")
    @POST("saveface")
    //Call<RequestBody> uploadImage();
    Call<RequestBody> saveFace(@Part MultipartBody.Part part, @Part("name") RequestBody requestBody,@Part("uniqueId") RequestBody reqBody);
}
