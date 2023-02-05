#![allow(non_snake_case)]

mod path;
mod world;

use pyo3::prelude::*;

#[pymodule]
fn janlukas(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    world::bind(py, m)?;
    path::bind(py, m)?;
    Ok(())
}
