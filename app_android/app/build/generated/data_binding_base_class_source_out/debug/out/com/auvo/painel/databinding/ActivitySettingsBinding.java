// Generated by view binder compiler. Do not edit!
package com.auvo.painel.databinding;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AutoCompleteTextView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.widget.Toolbar;
import androidx.viewbinding.ViewBinding;
import androidx.viewbinding.ViewBindings;
import com.auvo.painel.R;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.google.android.material.textfield.TextInputEditText;
import java.lang.NullPointerException;
import java.lang.Override;
import java.lang.String;

public final class ActivitySettingsBinding implements ViewBinding {
  @NonNull
  private final LinearLayout rootView;

  @NonNull
  public final MaterialButton btnLogout;

  @NonNull
  public final MaterialButton btnSaveSettings;

  @NonNull
  public final TextInputEditText etDueDays;

  @NonNull
  public final AutoCompleteTextView spinnerFrequency;

  @NonNull
  public final SwitchMaterial switchNotifications;

  @NonNull
  public final Toolbar toolbar;

  @NonNull
  public final TextView tvAppVersion;

  @NonNull
  public final TextView tvUserContracts;

  @NonNull
  public final TextView tvUserName;

  @NonNull
  public final TextView tvUserUsername;

  private ActivitySettingsBinding(@NonNull LinearLayout rootView, @NonNull MaterialButton btnLogout,
      @NonNull MaterialButton btnSaveSettings, @NonNull TextInputEditText etDueDays,
      @NonNull AutoCompleteTextView spinnerFrequency, @NonNull SwitchMaterial switchNotifications,
      @NonNull Toolbar toolbar, @NonNull TextView tvAppVersion, @NonNull TextView tvUserContracts,
      @NonNull TextView tvUserName, @NonNull TextView tvUserUsername) {
    this.rootView = rootView;
    this.btnLogout = btnLogout;
    this.btnSaveSettings = btnSaveSettings;
    this.etDueDays = etDueDays;
    this.spinnerFrequency = spinnerFrequency;
    this.switchNotifications = switchNotifications;
    this.toolbar = toolbar;
    this.tvAppVersion = tvAppVersion;
    this.tvUserContracts = tvUserContracts;
    this.tvUserName = tvUserName;
    this.tvUserUsername = tvUserUsername;
  }

  @Override
  @NonNull
  public LinearLayout getRoot() {
    return rootView;
  }

  @NonNull
  public static ActivitySettingsBinding inflate(@NonNull LayoutInflater inflater) {
    return inflate(inflater, null, false);
  }

  @NonNull
  public static ActivitySettingsBinding inflate(@NonNull LayoutInflater inflater,
      @Nullable ViewGroup parent, boolean attachToParent) {
    View root = inflater.inflate(R.layout.activity_settings, parent, false);
    if (attachToParent) {
      parent.addView(root);
    }
    return bind(root);
  }

  @NonNull
  public static ActivitySettingsBinding bind(@NonNull View rootView) {
    // The body of this method is generated in a way you would not otherwise write.
    // This is done to optimize the compiled bytecode for size and performance.
    int id;
    missingId: {
      id = R.id.btnLogout;
      MaterialButton btnLogout = ViewBindings.findChildViewById(rootView, id);
      if (btnLogout == null) {
        break missingId;
      }

      id = R.id.btnSaveSettings;
      MaterialButton btnSaveSettings = ViewBindings.findChildViewById(rootView, id);
      if (btnSaveSettings == null) {
        break missingId;
      }

      id = R.id.etDueDays;
      TextInputEditText etDueDays = ViewBindings.findChildViewById(rootView, id);
      if (etDueDays == null) {
        break missingId;
      }

      id = R.id.spinnerFrequency;
      AutoCompleteTextView spinnerFrequency = ViewBindings.findChildViewById(rootView, id);
      if (spinnerFrequency == null) {
        break missingId;
      }

      id = R.id.switchNotifications;
      SwitchMaterial switchNotifications = ViewBindings.findChildViewById(rootView, id);
      if (switchNotifications == null) {
        break missingId;
      }

      id = R.id.toolbar;
      Toolbar toolbar = ViewBindings.findChildViewById(rootView, id);
      if (toolbar == null) {
        break missingId;
      }

      id = R.id.tvAppVersion;
      TextView tvAppVersion = ViewBindings.findChildViewById(rootView, id);
      if (tvAppVersion == null) {
        break missingId;
      }

      id = R.id.tvUserContracts;
      TextView tvUserContracts = ViewBindings.findChildViewById(rootView, id);
      if (tvUserContracts == null) {
        break missingId;
      }

      id = R.id.tvUserName;
      TextView tvUserName = ViewBindings.findChildViewById(rootView, id);
      if (tvUserName == null) {
        break missingId;
      }

      id = R.id.tvUserUsername;
      TextView tvUserUsername = ViewBindings.findChildViewById(rootView, id);
      if (tvUserUsername == null) {
        break missingId;
      }

      return new ActivitySettingsBinding((LinearLayout) rootView, btnLogout, btnSaveSettings,
          etDueDays, spinnerFrequency, switchNotifications, toolbar, tvAppVersion, tvUserContracts,
          tvUserName, tvUserUsername);
    }
    String missingId = rootView.getResources().getResourceName(id);
    throw new NullPointerException("Missing required view with ID: ".concat(missingId));
  }
}
