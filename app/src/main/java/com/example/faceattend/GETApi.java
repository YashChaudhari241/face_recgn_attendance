package com.example.faceattend;

import org.json.JSONObject;

import java.util.List;

import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.Headers;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.Part;
import retrofit2.http.Query;

public interface GETApi {
    @Multipart
    @POST("checkface")
    Call<ResponseBody> checkface(
            @Query("name") String name,
            @Query("uniqueId") String uId,
            @Part MultipartBody.Part file
            //@Part ("description") RequestBody description
    );
    @Multipart
    @POST("saveface")
        //Call<RequestBody> uploadImage();
    Call<ResponseBody> saveFace(@Query("name") String name,
                                @Query("uniqueId") String uId,
                                @Part MultipartBody.Part file);
//    @GET("hello")
//    Call<DataModel> getHello();
    @POST("inituser")
        //on below line we are creating a method to post our data.
    Call<InitUserModel> verifyToken(@Header("Authorization") String token,@Body JsonObj priv);
}
