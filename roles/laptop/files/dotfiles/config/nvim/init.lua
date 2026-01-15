-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- Load plugins
require("lazy").setup(require("plugins"))

-- Appearance
vim.cmd.colorscheme("dracula")
vim.opt.number = true
vim.opt.cursorline = true
vim.opt.termguicolors = true

-- Indentation
vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.expandtab = true
vim.opt.tabstop = 2
vim.opt.shiftwidth = 2

-- Clipboard
vim.opt.clipboard = "unnamed"

-- Mouse
vim.opt.mouse = "a"

-- Undo
vim.opt.undofile = true

-- Key mappings
vim.keymap.set("n", "<leader>f", "<cmd>Files<cr>", { desc = "Find files (fzf)" })
vim.keymap.set("n", "<leader>g", "<cmd>Rg<cr>", { desc = "Grep (fzf)" })
vim.keymap.set("n", "<leader>b", "<cmd>Buffers<cr>", { desc = "Buffers (fzf)" })
vim.keymap.set("n", "<leader>h", "<cmd>History<cr>", { desc = "History (fzf)" })
vim.keymap.set("n", "<leader>/", "<cmd>BLines<cr>", { desc = "Search lines (fzf)" })
