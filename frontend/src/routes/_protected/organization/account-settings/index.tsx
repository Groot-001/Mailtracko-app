import { useState, useEffect, useRef } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Upload, Loader2, Mail, Phone, Globe, MapPin, Search, Edit2, Trash2 } from "lucide-react";
import { useAuthStore } from "../../../../shared/store/AuthStore";
import { updateProfile, uploadProfileImage, getCurrentUser } from "../../../../shared/api/authApi";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";
import { ConfirmDialog } from "../../../../shared/components/ConfirmDialog";
import { useToast } from "../../../../shared/hooks/useToast";

export const Route = createFileRoute("/_protected/organization/account-settings/")({
  loader: async () => {
    try {
      const user = await getCurrentUser();
      useAuthStore.getState().setUser(user);
      return user;
    } catch (err) {
      console.error("Loader failed to fetch current user:", err);
      return null;
    }
  },
  component: ProfilePage,
});

// ─── Country Code Definitions ──────────────────────────────────────────────────

interface Country {
  code: string;
  flag: string;
  name: string;
}

const COUNTRIES: Country[] = [
  { code: "+1", flag: "🇺🇸", name: "United States" },
  { code: "+91", flag: "🇮🇳", name: "India" },
  { code: "+977", flag: "🇳🇵", name: "Nepal" },
  { code: "+44", flag: "🇬🇧", name: "United Kingdom" },
  { code: "+61", flag: "🇦🇺", name: "Australia" },
  { code: "+1", flag: "🇨🇦", name: "Canada" },
  { code: "+81", flag: "🇯🇵", name: "Japan" },
  { code: "+49", flag: "🇩🇪", name: "Germany" },
  { code: "+33", flag: "🇫🇷", name: "France" },
  { code: "+86", flag: "🇨🇳", name: "China" },
  { code: "+7", flag: "🇷🇺", name: "Russia" },
  { code: "+55", flag: "🇧🇷", name: "Brazil" },
  { code: "+39", flag: "🇮🇹", name: "Italy" },
  { code: "+34", flag: "🇪🇸", name: "Spain" },
  { code: "+971", flag: "🇦🇪", name: "United Arab Emirates" },
  { code: "+65", flag: "🇸🇬", name: "Singapore" },
];

// ─── Timezone List ────────────────────────────────────────────────────────────

const TIMEZONES = [
  "Africa/Cairo", "Africa/Johannesburg", "Africa/Lagos", "Africa/Nairobi",
  "America/Anchorage", "America/Argentina/Buenos_Aires", "America/Chicago",
  "America/Denver", "America/Los_Angeles", "America/Mexico_City", "America/New_York",
  "America/Phoenix", "America/Sao_Paulo", "America/Vancouver", "Asia/Bangkok",
  "Asia/Colombo", "Asia/Dubai", "Asia/Hong_Kong", "Asia/Jakarta", "Asia/Kabul",
  "Asia/Karachi", "Asia/Kathmandu", "Asia/Kolkata", "Asia/Manila", "Asia/Seoul",
  "Asia/Singapore", "Asia/Taipei", "Asia/Tokyo", "Australia/Adelaide",
  "Australia/Brisbane", "Australia/Melbourne", "Australia/Perth", "Australia/Sydney",
  "Europe/Amsterdam", "Europe/Berlin", "Europe/Brussels", "Europe/London",
  "Europe/Madrid", "Europe/Moscow", "Europe/Paris", "Europe/Rome", "Pacific/Auckland",
  "Pacific/Honolulu", "UTC"
];

const toTitleCase = (str: string): string => {
  if (!str) return "";
  return str
    .toLowerCase()
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

function ProfilePage() {
  const loaderUser = Route.useLoaderData();
  const store = useAuthStore();
  // Prefer live Zustand state so mutations update every profile display immediately.
  const user = store.user || loaderUser;

  // Mode state
  const [isEditing, setIsEditing] = useState(false);
  const { showToast } = useToast();

  // Local Form States
  const [fullName, setFullName] = useState(() => toTitleCase(user?.full_name ?? ""));
  const [email, setEmail] = useState(user?.email ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [countryCode, setCountryCode] = useState(user?.country_code ?? "+1");
  const [timezone, setTimezone] = useState(user?.timezone ?? "UTC");
  const [location, setLocation] = useState(user?.location ?? "");
  const [profileImage, setProfileImage] = useState(user?.profile_image ?? "");

  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isRemovingImage, setIsRemovingImage] = useState(false);
  const [removePhotoOpen, setRemovePhotoOpen] = useState(false);
  const [dirty, setDirty] = useState(false);

  const resolvedFullName = dirty ? fullName : toTitleCase(user?.full_name ?? "");
  const resolvedEmail = dirty ? email : (user?.email ?? "");
  const resolvedPhone = dirty ? phone : (user?.phone ?? "");
  const resolvedCountryCode = dirty ? countryCode : (user?.country_code ?? "+1");
  const resolvedTimezone = dirty ? timezone : (user?.timezone ?? "UTC");
  const resolvedLocation = dirty ? location : (user?.location ?? "");
  const resolvedProfileImage = dirty ? profileImage : (user?.profile_image ?? "");

  // Custom Dropdown Open States
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [timezoneDropdownOpen, setTimezoneDropdownOpen] = useState(false);

  // Search Queries
  const [countrySearch, setCountrySearch] = useState("");
  const [timezoneSearch, setTimezoneSearch] = useState("");

  // Refs for click-away detection
  const countryRef = useRef<HTMLDivElement>(null);
  const timezoneRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Click-away listener
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (countryRef.current && !countryRef.current.contains(event.target as Node)) {
        setCountryDropdownOpen(false);
      }
      if (timezoneRef.current && !timezoneRef.current.contains(event.target as Node)) {
        setTimezoneDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleFieldChange = () => {
    if (!dirty) setDirty(true);
  };

  // Workable Multipart Image Upload
  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const allowedTypes = new Set(["image/png", "image/jpeg", "image/webp"]);
      const maxSize = 5 * 1024 * 1024;
      if (!allowedTypes.has(file.type)) {
        showToast("Profile photo must be a PNG, JPG, or WEBP file.", "error");
        e.target.value = "";
        return;
      }
      if (file.size === 0 || file.size > maxSize) {
        showToast("Profile photo must be non-empty and 5 MB or smaller.", "error");
        e.target.value = "";
        return;
      }

      const fallbackProfileImage = user?.profile_image ?? "";
      // 1. Render local preview immediately
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImage(reader.result as string);
      };
      reader.readAsDataURL(file);

      // 2. Perform upload
      setIsUploadingImage(true);
      try {
        const response = await uploadProfileImage(file);
        const uploadedUrl = response.url;
        if (uploadedUrl) {
          setProfileImage(uploadedUrl);
          // The upload endpoint persists the profile image immediately; keep
          // the global authenticated user in sync so the avatar updates without refresh.
          store.setUser({ ...response, profile_image: uploadedUrl });
          showToast("Profile photo uploaded successfully.", "success");
        }
      } catch (error: unknown) {
        setProfileImage(fallbackProfileImage);
        showToast(getApiErrorMessage(error, "Failed to upload image. Please try again."), "error");
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      } finally {
        setIsUploadingImage(false);
      }
    }
  };

  const handleRemoveProfileImage = async () => {
    setIsRemovingImage(true);
    try {
      const updatedUser = await updateProfile({ profile_image: "" });
      store.setUser(updatedUser);
      setProfileImage("");
      setRemovePhotoOpen(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      showToast("Profile photo removed successfully.", "success");
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, "Failed to remove profile photo."), "error");
    } finally {
      setIsRemovingImage(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const persistableProfileImage = resolvedProfileImage.startsWith("data:")
        ? (user?.profile_image ?? "")
        : resolvedProfileImage;

      const updatedUser = await updateProfile({
        full_name: resolvedFullName.trim(),
        phone: resolvedPhone.trim(),
        country_code: resolvedCountryCode.trim(),
        timezone: resolvedTimezone.trim(),
        location: resolvedLocation.trim(),
        profile_image: persistableProfileImage,
      });
      store.setUser(updatedUser);
      setFullName(toTitleCase(updatedUser.full_name ?? ""));
      setEmail(updatedUser.email ?? "");
      setPhone(updatedUser.phone ?? "");
      setCountryCode(updatedUser.country_code ?? "+1");
      setTimezone(updatedUser.timezone ?? "UTC");
      setLocation(updatedUser.location ?? "");
      setProfileImage(updatedUser.profile_image ?? "");
      setDirty(false);
      setIsEditing(false);
      showToast("Profile updated successfully", "success");
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, "Failed to update profile."), "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      setFullName(toTitleCase(user.full_name ?? ""));
      setEmail(user.email ?? "");
      setPhone(user.phone ?? "");
      setCountryCode(user.country_code ?? "+1");
      setTimezone(user.timezone ?? "UTC");
      setLocation(user.location ?? "");
      setProfileImage(user.profile_image ?? "");
      setDirty(false);
      setIsEditing(false);
    }
  };

  const filteredCountries = COUNTRIES.filter(
    (c) =>
      c.name.toLowerCase().includes(countrySearch.toLowerCase()) ||
      c.code.includes(countrySearch)
  );

  const filteredTimezones = TIMEZONES.filter((tz) =>
    tz.toLowerCase().includes(timezoneSearch.toLowerCase())
  );

  const selectedCountryObj = COUNTRIES.find((c) => c.code === resolvedCountryCode) || COUNTRIES[0];

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={removePhotoOpen}
        onOpenChange={setRemovePhotoOpen}
        title="Remove profile photo?"
        description="Your profile photo will be removed from your MailTracko account. You can upload another photo at any time."
        confirmLabel="Remove photo"
        isLoading={isRemovingImage}
        onConfirm={handleRemoveProfileImage}
      />
      {/* Notifications are rendered by the global top-right toast host. */}

      {/* Profile Settings Card */}
      <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-[#1A1C1C]">
              Profile Information
            </h2>
            <p className="text-xs text-[#4C4736] mt-0.5">
              {isEditing ? "Update your personal and professional details." : "View your personal and professional details."}
            </p>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
            >
              <Edit2 className="w-3.5 h-3.5 text-[#8F740D]" />
              Edit Profile
            </button>
          )}
        </div>

        {/* View Mode Layout */}
        {!isEditing ? (
          <div className="space-y-6 pt-2 border-t border-[#F4F3F3]">
            {/* Avatar & Basic Info */}
            <div className="flex items-center gap-5">
              {resolvedProfileImage ? (
                <img
                  src={resolvedProfileImage}
                  alt={resolvedFullName}
                  className="w-20 h-20 rounded-full object-cover border border-[#CEC6B0]/40 bg-[#F4F3F3]"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#F1D442]/40 to-[#E2C635]/20 border border-[#CEC6B0]/40 flex items-center justify-center font-bold text-2xl text-[#8F740D]">
                  {fullName ? fullName[0].toUpperCase() : "U"}
                </div>
              )}
              <div>
                <h3 className="text-lg font-bold text-[#1A1C1C]">{resolvedFullName || "Not Provided"}</h3>
                <p className="text-xs text-[#4C4736] mt-0.5">Workspace Collaborator</p>
              </div>
            </div>

            {/* Static Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 pt-2">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-[#4C4736] uppercase tracking-wide">Full Name</span>
                <p className="text-sm font-semibold text-[#1A1C1C]">{resolvedFullName || "—"}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-bold text-[#4C4736] uppercase tracking-wide">Work Email</span>
                <p className="text-sm font-semibold text-[#4C4736] opacity-70 flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5" />
                  {resolvedEmail} (locked)
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-bold text-[#4C4736] uppercase tracking-wide">Phone Number</span>
                <p className="text-sm font-semibold text-[#1A1C1C] flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-[#4C4736]" />
                  <span>{selectedCountryObj.flag} {selectedCountryObj.code} {resolvedPhone || "—"}</span>
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-bold text-[#4C4736] uppercase tracking-wide">Time Zone</span>
                <p className="text-sm font-semibold text-[#1A1C1C] flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-[#4C4736]" />
                  {resolvedTimezone}
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-bold text-[#4C4736] uppercase tracking-wide">Location</span>
                <p className="text-sm font-semibold text-[#1A1C1C] flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-[#4C4736]" />
                  {resolvedLocation || "—"}
                </p>
              </div>
            </div>
          </div>
        ) : (
          /* Editable Mode Layout */
          <>
            {/* Profile Image Row */}
            <div className="flex items-center gap-5 pt-2 border-t border-[#F4F3F3]">
              <div className="relative">
                {resolvedProfileImage ? (
                  <img
                    src={resolvedProfileImage}
                    alt={resolvedFullName}
                    className={`w-20 h-20 rounded-full object-cover border border-[#CEC6B0]/40 bg-[#F4F3F3] ${
                      isUploadingImage ? "opacity-40" : ""
                    }`}
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#F1D442]/40 to-[#E2C635]/20 border border-[#CEC6B0]/40 flex items-center justify-center font-bold text-2xl text-[#8F740D]">
                    {resolvedFullName ? resolvedFullName[0].toUpperCase() : "U"}
                  </div>
                )}
                {isUploadingImage && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-[#8F740D]" />
                  </div>
                )}
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-3">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleImageChange}
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-[#CEC6B0]/60 rounded-xl text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    Upload new photo
                  </button>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="text-xs font-bold text-[#8F740D] hover:underline cursor-pointer"
                  >
                    Change photo
                  </button>
                  {resolvedProfileImage ? (
                    <button
                      type="button"
                      onClick={() => setRemovePhotoOpen(true)}
                      disabled={isUploadingImage || isRemovingImage || isSaving}
                      className="flex items-center gap-1 text-xs font-semibold text-red-600 hover:text-red-700 hover:underline transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                      aria-label="Remove profile photo"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Remove photo</span>
                    </button>
                  ) : null}
                </div>
                <p className="text-[10px] text-[#4C4736]">PNG, JPG or WEBP. Max 5 MB.</p>
              </div>
            </div>

            {/* Form Fields */}
            <div className="space-y-4 pt-2">
              {/* Full Name */}
              <div className="space-y-1.5">
                <label htmlFor="prof-name" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Full Name
                </label>
                <input
                  id="prof-name"
                  type="text"
                  value={resolvedFullName}
                  maxLength={50}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    handleFieldChange();
                  }}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all"
                />
              </div>

              {/* Work Email (Locked / Disabled) */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Work Email
                </label>
                <input
                  type="email"
                  value={resolvedEmail}
                  readOnly
                  className="w-full px-3 py-2.5 rounded-xl border border-[#CEC6B0]/30 text-sm text-[#4C4736] bg-[#F4F3F3] cursor-not-allowed outline-none select-none"
                />
              </div>

              {/* Phone Number Grid */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Phone Number
                </label>
                <div className="flex gap-3">
                  {/* Country Code Dropdown with Search */}
                  <div className="relative w-36 shrink-0" ref={countryRef}>
                    <button
                      type="button"
                      onClick={() => setCountryDropdownOpen(!countryDropdownOpen)}
                      className="w-full px-3 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all flex items-center justify-between text-left cursor-pointer"
                    >
                      <span className="flex items-center gap-1.5">
                        <span>{selectedCountryObj.flag}</span>
                        <span>{selectedCountryObj.code}</span>
                      </span>
                      <span className="text-xs text-[#4C4736]">▼</span>
                    </button>

                    {countryDropdownOpen && (
                      <div className="absolute left-0 mt-1.5 w-64 bg-white border border-[#CEC6B0]/40 rounded-xl shadow-lg z-20 overflow-hidden flex flex-col max-h-60">
                        <div className="p-2 border-b border-[#F4F3F3] flex items-center gap-2 bg-[#F9F9F9]">
                          <Search className="w-3.5 h-3.5 text-[#CEC6B0] shrink-0" />
                          <input
                            type="text"
                            placeholder="Search code..."
                            value={countrySearch}
                            onChange={(e) => setCountrySearch(e.target.value)}
                            className="w-full text-xs bg-transparent outline-none text-[#1A1C1C]"
                            autoFocus
                          />
                        </div>
                        <div className="overflow-y-auto py-1">
                          {filteredCountries.map((c) => (
                            <button
                              key={`${c.code}-${c.name}`}
                              type="button"
                              onClick={() => {
                                setCountryCode(c.code);
                                setCountryDropdownOpen(false);
                                setCountrySearch("");
                                handleFieldChange();
                              }}
                              className="w-full px-3 py-2 text-left text-xs hover:bg-[#F4F3F3] transition-colors flex items-center justify-between cursor-pointer"
                            >
                              <span className="flex items-center gap-2">
                                <span>{c.flag}</span>
                                <span className="font-semibold">{c.name}</span>
                              </span>
                              <span className="text-[#4C4736]">{c.code}</span>
                            </button>
                          ))}
                          {filteredCountries.length === 0 && (
                            <p className="text-[10px] text-[#4C4736] text-center py-3">No codes found</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Phone number input */}
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={resolvedPhone}
                      maxLength={50}
                      onChange={(e) => {
                        setPhone(e.target.value);
                        handleFieldChange();
                      }}
                      placeholder="Enter phone number"
                      className="w-full px-3 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all"
                    />
                  </div>
                </div>
              </div>

              {/* Time Zone with Search */}
              <div className="space-y-1.5" ref={timezoneRef}>
                <label className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Time Zone
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setTimezoneDropdownOpen(!timezoneDropdownOpen)}
                    className="w-full px-3 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all flex items-center justify-between text-left cursor-pointer"
                  >
                    <span>{resolvedTimezone}</span>
                    <span className="text-xs text-[#4C4736]">▼</span>
                  </button>

                  {timezoneDropdownOpen && (
                    <div className="absolute left-0 right-0 mt-1.5 bg-white border border-[#CEC6B0]/40 rounded-xl shadow-lg z-20 overflow-hidden flex flex-col max-h-64">
                      <div className="p-2 border-b border-[#F4F3F3] flex items-center gap-2 bg-[#F9F9F9]">
                        <Search className="w-3.5 h-3.5 text-[#CEC6B0] shrink-0" />
                        <input
                          type="text"
                          placeholder="Search timezone..."
                          value={timezoneSearch}
                          onChange={(e) => setTimezoneSearch(e.target.value)}
                          className="w-full text-xs bg-transparent outline-none text-[#1A1C1C]"
                          autoFocus
                        />
                      </div>
                      <div className="overflow-y-auto py-1">
                        {filteredTimezones.map((tz) => (
                          <button
                            key={tz}
                            type="button"
                            onClick={() => {
                              setTimezone(tz);
                              setTimezoneDropdownOpen(false);
                              setTimezoneSearch("");
                              handleFieldChange();
                            }}
                            className="w-full px-3 py-2.5 text-left text-xs hover:bg-[#F4F3F3] transition-colors cursor-pointer"
                          >
                            {tz}
                          </button>
                        ))}
                        {filteredTimezones.length === 0 && (
                          <p className="text-[10px] text-[#4C4736] text-center py-3">No timezones found</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Location */}
              <div className="space-y-1.5">
                <label htmlFor="prof-location" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Location
                </label>
                <div className="relative flex items-center">
                  <MapPin className="absolute left-3 w-4 h-4 text-[#4C4736] pointer-events-none" />
                  <input
                    id="prof-location"
                    type="text"
                    value={resolvedLocation}
                    maxLength={255}
                    onChange={(e) => {
                      setLocation(e.target.value);
                      handleFieldChange();
                    }}
                    placeholder="e.g. Mumbai, India"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm text-[#1A1C1C] bg-white focus:outline-none focus:ring-2 focus:ring-[#F1D442]/50 focus:border-[#8F740D] transition-all"
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Sticky footer only in edit mode */}
      {isEditing && (
        <div className="sticky bottom-0 bg-white border-t border-[#EEEEEE] -mx-6 lg:-mx-8 px-6 lg:px-8 py-4 flex items-center justify-end gap-3 z-10 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <button
            onClick={handleCancel}
            className="px-5 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm font-medium text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors cursor-pointer bg-white"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!dirty || isSaving}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <span>Save Changes</span>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
