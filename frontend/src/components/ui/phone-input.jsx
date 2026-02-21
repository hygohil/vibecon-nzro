import * as React from "react"
import { cn } from "../../lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select"
import { Input } from "./input"

const countryCodes = [
  { code: "+91", country: "IN", flag: "🇮🇳", name: "India" },
  { code: "+1", country: "US", flag: "🇺🇸", name: "United States" },
  { code: "+44", country: "GB", flag: "🇬🇧", name: "United Kingdom" },
  { code: "+86", country: "CN", flag: "🇨🇳", name: "China" },
  { code: "+81", country: "JP", flag: "🇯🇵", name: "Japan" },
  { code: "+82", country: "KR", flag: "🇰🇷", name: "South Korea" },
  { code: "+49", country: "DE", flag: "🇩🇪", name: "Germany" },
  { code: "+33", country: "FR", flag: "🇫🇷", name: "France" },
  { code: "+61", country: "AU", flag: "🇦🇺", name: "Australia" },
  { code: "+55", country: "BR", flag: "🇧🇷", name: "Brazil" },
  { code: "+7", country: "RU", flag: "🇷🇺", name: "Russia" },
  { code: "+27", country: "ZA", flag: "🇿🇦", name: "South Africa" },
  { code: "+234", country: "NG", flag: "🇳🇬", name: "Nigeria" },
  { code: "+52", country: "MX", flag: "🇲🇽", name: "Mexico" },
  { code: "+62", country: "ID", flag: "🇮🇩", name: "Indonesia" },
  { code: "+92", country: "PK", flag: "🇵🇰", name: "Pakistan" },
  { code: "+880", country: "BD", flag: "🇧🇩", name: "Bangladesh" },
  { code: "+94", country: "LK", flag: "🇱🇰", name: "Sri Lanka" },
  { code: "+977", country: "NP", flag: "🇳🇵", name: "Nepal" },
  { code: "+971", country: "AE", flag: "🇦🇪", name: "UAE" },
  { code: "+966", country: "SA", flag: "🇸🇦", name: "Saudi Arabia" },
  { code: "+60", country: "MY", flag: "🇲🇾", name: "Malaysia" },
  { code: "+65", country: "SG", flag: "🇸🇬", name: "Singapore" },
  { code: "+66", country: "TH", flag: "🇹🇭", name: "Thailand" },
  { code: "+84", country: "VN", flag: "🇻🇳", name: "Vietnam" },
  { code: "+63", country: "PH", flag: "🇵🇭", name: "Philippines" },
]

export function PhoneInput({ value = "", onChange, className, placeholder = "Enter phone number", disabled, ...props }) {
  // Parse existing value
  const parsePhoneValue = (val) => {
    if (!val) return { countryCode: "+91", number: "" }
    
    // Find matching country code
    for (const country of countryCodes) {
      if (val.startsWith(country.code)) {
        return {
          countryCode: country.code,
          number: val.slice(country.code.length)
        }
      }
    }
    
    // Default to +91 if no match
    return { countryCode: "+91", number: val }
  }

  const parsed = parsePhoneValue(value)
  const [countryCode, setCountryCode] = React.useState(parsed.countryCode)
  const [number, setNumber] = React.useState(parsed.number)

  // Update parent when either changes
  React.useEffect(() => {
    const fullNumber = number ? `${countryCode}${number}` : ""
    if (onChange && fullNumber !== value) {
      onChange({ target: { value: fullNumber } })
    }
  }, [countryCode, number])

  // Update local state when value prop changes externally
  React.useEffect(() => {
    const parsed = parsePhoneValue(value)
    setCountryCode(parsed.countryCode)
    setNumber(parsed.number)
  }, [value])

  return (
    <div className={cn("flex gap-2", className)}>
      <Select value={countryCode} onValueChange={setCountryCode} disabled={disabled}>
        <SelectTrigger className="w-[140px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {countryCodes.map((country) => (
            <SelectItem key={country.code} value={country.code}>
              <span className="flex items-center gap-2">
                <span>{country.flag}</span>
                <span className="text-xs">{country.code}</span>
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Input
        type="tel"
        value={number}
        onChange={(e) => setNumber(e.target.value.replace(/[^0-9]/g, ''))}
        placeholder={placeholder}
        className="flex-1"
        disabled={disabled}
        {...props}
      />
    </div>
  )
}
