import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import React from "react";

type Props = {
  handleChange: any;
  labelId:string,
  selectId:string,
  label:string,
};

export default function TypeSelector({labelId, label,selectId, handleChange }: Props) {
  return (
    <>
      <InputLabel id={labelId}>{label}</InputLabel>
      <Select
        labelId={labelId}
        id={selectId}
        label={label}
        onChange={handleChange}
      >
        <MenuItem value="industry">Industry</MenuItem>
        <MenuItem value="company">Company</MenuItem>
        <MenuItem value="founder">Founder</MenuItem>
      </Select>
      </>
  );
}
