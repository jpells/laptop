return {
  -- Dracula colorscheme
  {
    "dracula/vim",
    name = "dracula",
    lazy = false,
    priority = 1000,
  },
  -- FZF
  { "junegunn/fzf", build = ":call fzf#install()" },
  { "junegunn/fzf.vim" },
  -- Which-key
  { "folke/which-key.nvim", event = "VeryLazy" },
}
